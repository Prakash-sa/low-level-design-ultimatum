# Leaderboard — Complete Design Guide

> Real-time ranking system tracking player scores and displaying top performers globally or by region, with caching, seasonal resets, and percentile computation.

**Scale**: 10M+ players, 100K QPS, sub-100ms leaderboard queries  
**Duration**: 75-minute interview guide  
**Focus**: Sorted ranking structures, cache invalidation, regional partitioning, season lifecycle

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Step 01: The Setup — Clarify Requirements](#step-01-the-setup--clarify-requirements)
3. [Step 02: Structure — Define Entities](#step-02-structure--define-entities)
4. [Step 03: Interface — APIs & Entry Points](#step-03-interface--apis--entry-points)
5. [Step 04: Architecture — Relationships & Diagram](#step-04-architecture--relationships--diagram)
6. [Step 05: Optimization — Design Patterns](#step-05-optimization--design-patterns)
7. [Step 06: Implementation — Code & Concurrency](#step-06-implementation--code--concurrency)
8. [Demo Scenarios](#demo-scenarios)
9. [Interview Q&A](#interview-qa)
10. [Scaling Q&A](#scaling-qa)
11. [Success Checklist](#success-checklist)

---

## Quick Start

**5-Minute Overview for Last-Minute Prep**

### What Problem Are We Solving?
Players score points during gameplay → scores accumulate across events → ranks are computed globally and by region → top-N lists are served with low latency → leaderboards reset on season boundaries. Core concerns: efficient sorted ranking for millions of players, cache freshness, and thread-safe score updates.

### Core Flow
```
Player Scores → record_score() → Update Player Totals → Invalidate Cache
                                                               ↓
Query top-100  ←────────────────── Serve Cached Result ← Recompute Rankings
                                         ↑ TTL 5 min
                              (global / regional / nearby)
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single machine or distributed?** → "Distributed system with 10M+ players"
2. **Global only or regional leaderboards?** → "Both global and per-region"
3. **Real-time or batch ranking updates?** → "Batch with cache TTL acceptable"
4. **Time-windowed leaderboards (daily/weekly)?** → "Yes — daily, weekly, monthly, all-time"
5. **Season resets?** → "Yes, seasonal archives and fresh-start each season"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Player** | Competes and checks rank | Score points, query personal rank, see nearby competitors |
| **Game Server** | Records score events | Submit score updates, batch score events |
| **Admin** | Manages seasons and regions | Start/end seasons, create regions, archive leaderboards |
| **System** | Cache + rank coordinator | Recompute rankings, invalidate TTL cache, broadcast updates |

### Functional Requirements (What does the system do?)

✅ **Score Recording**
  - Accept score update events from game servers in real-time
  - Accumulate scores per time window (daily, weekly, monthly, all-time)
  - Record full event history (event type, timestamp, points)

✅ **Ranking Computation**
  - Compute global top-N rankings sorted by score descending
  - Tiebreak by earliest timestamp (first to reach score wins)
  - Compute per-region top-N rankings

✅ **Leaderboard Queries**
  - Query top-100 (or top-N) global or regional leaderboard
  - Query a single player's rank, score, and percentile
  - Query "nearby" competitors (player ± offset ranks)

✅ **Seasonal Management**
  - Archive current leaderboard at season end
  - Reset all scores for new season
  - Award badges to top finishers

✅ **Caching**
  - Cache top-N results with a configurable TTL (default 5 minutes)
  - Invalidate or recompute on cache miss

### Non-Functional Requirements (How does it perform?)

✅ **Latency**: Leaderboard query < 100ms (served from cache)  
✅ **Throughput**: 100K QPS score updates  
✅ **Scale**: 10M+ players per leaderboard  
✅ **Consistency**: Rankings consistent within TTL window (eventual)  
✅ **Uptime**: 99.99% (competitive ranked games require high availability)  
✅ **Update Latency**: Score visible in rankings within 1 second of batch flush  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Max players** | 10M+ per leaderboard |
| **Scoring range** | 0 – 1,000,000,000 points |
| **Top-N display** | Typically 100–1000 entries |
| **Cache TTL** | 5 minutes (configurable) |
| **Tiebreaker** | Earlier timestamp wins |
| **Season length** | ~3 months; configurable |
| **Regional partitions** | By account setting or geo-IP |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

From the requirements above, identify nouns:

```
Player, Score, Leaderboard, Region, Season, Cache, TimeRange, Ranking, ...
```

### Step 2.2: Define Core Classes

#### **Player** — A participant tracked by the ranking system
```
Properties:
  - player_id: str (unique identifier)
  - name: str
  - region: str (geo partition, e.g. "USA")
  - all_time_score: int
  - daily_score: int
  - weekly_score: int
  - monthly_score: int
  - last_update: datetime (used for tiebreaking)

Behaviors:
  - (data holder — score updates applied by Leaderboard)
```

#### **Score** — A single scoring event
```
Properties:
  - event_id: str
  - player_id: str
  - points: int
  - timestamp: datetime
  - event_type: str (e.g. "game_win", "kill", "achievement")

Behaviors:
  - (immutable record)
```

#### **Leaderboard** — Central ranking controller (Singleton)
```
Properties:
  - players: Dict[str, Player]
  - scores: List[Score]
  - global_top_100: List[Tuple[player_id, score]]
  - regional_tops: Dict[region, List[Tuple[player_id, score]]]
  - cache_timestamp: datetime
  - cache_ttl_seconds: int

Behaviors:
  - add_player(player_id, name, region): Register player
  - record_score(player_id, points, event_type): Accept score event
  - get_global_leaderboard(limit): Query top-N globally
  - get_regional_leaderboard(region, limit): Query top-N by region
  - get_player_rank(player_id): Get rank, score, percentile
  - get_nearby_players(player_id, offset): Get surrounding ranks
  - _recompute_rankings(): Rebuild sorted cache from player scores
  - _is_cache_valid(): Check if cache TTL has expired
```

### Step 2.3: Enumerations and Data Classes

```python
class TimeRange(Enum):
    DAILY   = "daily"
    WEEKLY  = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"

@dataclass
class Player:
    player_id: str
    name: str
    region: str
    all_time_score: int = 0
    daily_score: int = 0
    weekly_score: int = 0
    monthly_score: int = 0
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class Score:
    event_id: str
    player_id: str
    points: int
    timestamp: datetime
    event_type: str
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Player** | Stores accumulated scores and region | Can't rank or partition players |
| **Score** | Immutable event audit trail | Can't recompute or audit scores |
| **Leaderboard** | Central ranking + cache controller | No coordination for concurrent queries |
| **TimeRange** | Scopes queries to windows | Can't support daily/weekly resets |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Add Player**
```python
def add_player(player_id: str, name: str, region: str) -> None:
    """
    Register a new player in the leaderboard system.
    Raises: DuplicatePlayerError if player_id already exists.
    Thread-safe: YES
    """
    pass
```

#### **2. Record Score** ⭐ CRITICAL
```python
def record_score(player_id: str, points: int, event_type: str) -> None:
    """
    Accept a scoring event and update all applicable score windows.

    Precondition: player_id must be registered.
    Postcondition: player.all_time_score += points; cache invalidated.

    Raises: PlayerNotFoundError if player not registered.
    Thread-safe: YES — guarded by RLock
    Response Time: <10ms (in-memory update)
    """
    pass
```

#### **3. Query Global Leaderboard** ⭐ CRITICAL
```python
def get_global_leaderboard(limit: int = 100) -> List[Tuple[int, str, int]]:
    """
    Return top-N global players sorted by score descending.

    Returns: [(rank, player_id, score), ...]
    Cache: served from in-memory cache if TTL valid; recomputed otherwise.
    Response Time: <100ms
    """
    pass
```

#### **4. Query Regional Leaderboard**
```python
def get_regional_leaderboard(region: str, limit: int = 100) -> List[Tuple[int, str, int]]:
    """
    Return top-N players within a specific region.

    Returns: [(rank, player_id, score), ...]
    Raises: RegionNotFoundError if region has no players.
    """
    pass
```

#### **5. Query Player Rank**
```python
def get_player_rank(player_id: str) -> Optional[Tuple[int, int, float]]:
    """
    Return rank, score, and percentile for a specific player.

    Returns: (rank, score, percentile)
      - percentile = (players_below / total) * 100
    Returns None if player not registered.
    """
    pass
```

#### **6. Query Nearby Competitors**
```python
def get_nearby_players(player_id: str, offset: int = 5) -> List[Tuple[int, str, int]]:
    """
    Return players at ranks [player_rank - offset, player_rank + offset].

    Returns: [(rank, player_id, score), ...]
    Useful for: showing competition context around a player's position.
    """
    pass
```

### Step 3.2: Failure Model

```python
class LeaderboardException(Exception):
    """Base exception"""
    pass

class PlayerNotFoundError(LeaderboardException):
    """player_id not registered"""
    pass

class RegionNotFoundError(LeaderboardException):
    """No players exist in requested region"""
    pass
```

### Step 3.3: API Usage Example

```python
lb = Leaderboard()

# Register players
lb.add_player("P001", "Alice", "USA")
lb.add_player("P002", "Bob", "EU")

# Record score events
lb.record_score("P001", 5000, "game_win")
lb.record_score("P002", 3000, "kill_streak")

# Query top leaderboard
top = lb.get_global_leaderboard(limit=10)
for rank, pid, score in top:
    print(f"Rank {rank}: {pid} — {score} pts")

# Query single player
rank, score, percentile = lb.get_player_rank("P001")
print(f"Alice: rank={rank}, score={score}, top {100-percentile:.1f}%")

# Nearby competitors
nearby = lb.get_nearby_players("P001", offset=5)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and inheritance. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
Leaderboard HAS-A players (1:N Composition)
  └─ Leaderboard owns and manages all Player objects

Leaderboard HAS-A scores (1:N Composition)
  └─ Leaderboard stores all Score events as audit trail

Leaderboard HAS-A global_top_100 (1:N, Cache)
  └─ Computed view over players; invalidated by TTL

Leaderboard HAS-A regional_tops (1:N, Cache)
  └─ Per-region computed views; same TTL mechanism

Score REFERENCES Player (1:1 Association)
  └─ Score records which player earned points (no ownership)

Player belongs-to Region (N:1 Association)
  └─ Many players share a region string
```

### Step 4.2: Complete UML Class Diagram

```
┌───────────────────────────────────────────────────┐
│              Leaderboard (Singleton)               │
├───────────────────────────────────────────────────┤
│ - _instance: Leaderboard                          │
│ - _lock: threading.Lock          (class-level)    │
│ - players: Dict[str, Player]                      │
│ - scores: List[Score]                             │
│ - global_top_100: List[Tuple[str, int]]           │
│ - regional_tops: Dict[str, List[Tuple[str, int]]] │
│ - cache_timestamp: datetime                       │
│ - cache_ttl_seconds: int                          │
│ - lock: threading.RLock          (instance-level) │
├───────────────────────────────────────────────────┤
│ + add_player(id, name, region): void              │
│ + record_score(id, pts, type): void               │
│ + get_global_leaderboard(limit): List             │
│ + get_regional_leaderboard(region, limit): List   │
│ + get_player_rank(id): Tuple                      │
│ + get_nearby_players(id, offset): List            │
│ + display_leaderboard(limit): void                │
│ - _is_cache_valid(): bool                         │
│ - _recompute_rankings(): void                     │
└───────────────────────────────────────────────────┘
           │ owns 1:N
           ▼
    ┌──────────────────────────────────┐
    │             Player               │
    ├──────────────────────────────────┤
    │ - player_id: str                 │
    │ - name: str                      │
    │ - region: str                    │
    │ - all_time_score: int            │
    │ - daily_score: int               │
    │ - weekly_score: int              │
    │ - monthly_score: int             │
    │ - last_update: datetime          │
    └──────────────────────────────────┘

           │ records 1:N
           ▼
    ┌──────────────────────────────────┐
    │              Score               │
    ├──────────────────────────────────┤
    │ - event_id: str                  │
    │ - player_id: str                 │
    │ - points: int                    │
    │ - timestamp: datetime            │
    │ - event_type: str                │
    └──────────────────────────────────┘


CACHE LAYER:
┌──────────────────────────────────────────────────┐
│             CachedRankings (in Leaderboard)       │
├──────────────────────────────────────────────────┤
│  global_top_100   → Top 100 players (score DESC) │
│  regional_tops    → Per-region Top 100            │
│  cache_timestamp  → When cache was last built     │
│  cache_ttl        → 5-minute expiry               │
└──────────────────────────────────────────────────┘
              ↑ recomputed when TTL expires

ENUM:
┌─────────────────────────────┐
│         TimeRange           │
├─────────────────────────────┤
│ DAILY / WEEKLY / MONTHLY /  │
│ ALL_TIME                    │
└─────────────────────────────┘
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| Leaderboard → Players | 1:N | Composition | System owns all player objects |
| Leaderboard → Scores | 1:N | Composition | System owns all score events |
| Leaderboard → global_top_100 | 1:N | Aggregation (Cache) | Computed view, invalidated by TTL |
| Leaderboard → regional_tops | 1:N | Aggregation (Cache) | One per region, same TTL |
| Score → Player | N:1 | Association | Score references owning player |
| Player → Region | N:1 | Association | Many players share one region |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems. Discuss data-structure choice explicitly.

### Data Structure Choice: Sorted Set vs Heap vs Skip List

| Structure | Insert | Top-K Query | Rank Lookup | Memory | Best For |
|-----------|--------|-------------|-------------|--------|----------|
| **Sorted Array (re-sort)** | O(n log n) | O(k) | O(log n) | Low | Small N, batch updates |
| **Min-Heap of top-K** | O(log k) | O(k) | O(n) | O(k) | Top-K maintenance only |
| **Redis Sorted Set (ZSET)** | O(log n) | O(k) | O(log n) | Medium | Production distributed |
| **Skip List** | O(log n) | O(k) | O(log n) | Medium | Custom in-memory DB |
| **Balanced BST (AVL/RB)** | O(log n) | O(k) | O(log n) | Medium | General purpose |

**Interview recommendation**: Use sorted array + batch recompute for the in-memory interview implementation. In production, use Redis Sorted Sets (ZSETs) which are skip-list backed and support all needed operations natively.

---

### Pattern 1: **Singleton** (For Leaderboard)

**Problem**: Multiple threads and services must share a single consistent view of rankings and player scores.

**Solution**: One global Leaderboard instance, thread-safe initialization with double-checked locking.

```python
class Leaderboard:
    _instance = None
    _lock = threading.Lock()          # Class-level lock for Singleton creation

    def __new__(cls, *args, **kwargs):  # Accept *args/**kwargs so subclasses don't break
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.lock = threading.RLock()  # RLock: reentrant — outer method can call inner
        # ... rest of init
```

**Benefit**: Single source of truth, thread-safe initialization, global access point  
**Trade-off**: Global state (harder to unit-test), cannot horizontally scale without distributed coordination

---

### Pattern 2: **Cache with TTL** (For Rankings)

**Problem**: Ranking 10M players on every query is O(n log n) — too expensive at 100K QPS.

**Solution**: Compute and cache top-N results; serve from cache until TTL expires.

```python
def _is_cache_valid(self) -> bool:
    return (datetime.now() - self.cache_timestamp).total_seconds() < self.cache_ttl_seconds

def get_global_leaderboard(self, limit: int = 100):
    with self.lock:
        if not self._is_cache_valid():   # Cache miss: recompute
            self._recompute_rankings()   # Safe: RLock allows re-entry
        return [(rank+1, pid, score)
                for rank, (pid, score) in enumerate(self.global_top_100[:limit])]
```

**Benefit**: O(1) query latency from cache (sub-millisecond), amortized O(n log n) over TTL period  
**Trade-off**: Rankings may be stale by up to TTL seconds (5 min by default)

---

### Pattern 3: **Observer** (For Rank-Change Notifications)

**Problem**: Rank promotions/demotions (e.g., entering top-10) should trigger notifications — but ranking logic should not know about email/SMS.

**Solution**: Observer pattern decouples ranking computation from notification delivery.

```python
class RankObserver(ABC):
    @abstractmethod
    def on_rank_change(self, player_id: str, old_rank: int, new_rank: int):
        pass

class ConsoleRankObserver(RankObserver):
    def on_rank_change(self, player_id, old_rank, new_rank):
        direction = "↑" if new_rank < old_rank else "↓"
        print(f"[RANK {direction}] {player_id}: {old_rank} → {new_rank}")

# Register during setup:
leaderboard.add_rank_observer(ConsoleRankObserver())
```

**Benefit**: Loose coupling — add Slack/SMS/push notifiers without changing Leaderboard code  
**Trade-off**: Observer lifecycle and ordering must be managed; slow observers block notifications

---

### Pattern 4: **Strategy** (For Ranking Algorithms)

**Problem**: Different games may rank by ELO rating, raw points, win percentage, or composite score.

**Solution**: Pluggable ranking strategy — swap algorithm without modifying Leaderboard internals.

```python
class RankingStrategy(ABC):
    @abstractmethod
    def score_key(self, player: Player) -> tuple:
        pass

class PointsRanking(RankingStrategy):
    def score_key(self, player: Player) -> tuple:
        return (-player.all_time_score, player.last_update)

class WinRateRanking(RankingStrategy):
    def score_key(self, player: Player) -> tuple:
        # hypothetical: would use player.wins / player.games
        return (-player.all_time_score, player.last_update)

# Usage:
leaderboard.set_ranking_strategy(WinRateRanking())
```

**Benefit**: Easy to add new ranking schemes (ELO, composite) without modifying core logic  
**Trade-off**: Extra abstraction layer; strategy must be kept consistent across recomputes

---

### Pattern 5: **State Machine** (For Season Lifecycle)

**Problem**: Seasons transition ACTIVE → CLOSING → ARCHIVED. Invalid transitions (e.g., re-activating an archived season) must be prevented.

**Solution**: Enum-based state with guarded transition methods.

```python
class SeasonStatus(Enum):
    ACTIVE   = "active"
    CLOSING  = "closing"   # Awards being distributed
    ARCHIVED = "archived"  # Historical; read-only

def close_season(season):
    if season.status != SeasonStatus.ACTIVE:
        raise InvalidTransitionError("Can only close ACTIVE seasons")
    season.status = SeasonStatus.CLOSING
    # ... award badges, archive leaderboard
    season.status = SeasonStatus.ARCHIVED
```

**Benefit**: Explicit lifecycle, invalid transitions caught at runtime, clear audit trail  
**Trade-off**: Must maintain transition logic; doesn't auto-enforce all edge cases

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|----------------|---------|
| **Singleton** | Single consistent view of all rankings | Global access, no duplicate state |
| **Cache + TTL** | O(n log n) ranking is too expensive per query | Sub-100ms query latency at scale |
| **Observer** | Rank-change events trigger notifications | Decoupled, extensible notification |
| **Strategy** | Different scoring/ranking algorithms | Pluggable ranking without core changes |
| **State Machine** | Season lifecycle transitions | Invalid transitions prevented |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Use `RLock` when the same lock may be re-entered within the call stack.

### Bug Fixes Applied

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `__new__(cls)` rejects subclass args | `super().__new__(cls)` receives extra args | Changed to `__new__(cls, *args, **kwargs)` |
| `threading.Lock()` deadlocks on re-entry | `get_global_leaderboard` holds lock, calls `_recompute_rankings` which tries to re-acquire | Changed instance lock to `threading.RLock()` |

### Complete Thread-Safe Implementation

```python
"""
Leaderboard - Interview Implementation
Demonstrates:
1. Real-time ranking computation
2. Caching top-N results with TTL
3. Percentile calculation
4. Regional partitioning
5. Seasonal management
"""

from enum import Enum
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import heapq

# ============================================================================
# ENUMERATIONS
# ============================================================================

class TimeRange(Enum):
    DAILY    = "daily"
    WEEKLY   = "weekly"
    MONTHLY  = "monthly"
    ALL_TIME = "all_time"

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Player:
    player_id: str
    name: str
    region: str
    all_time_score: int = 0
    daily_score: int = 0
    weekly_score: int = 0
    monthly_score: int = 0
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class Score:
    event_id: str
    player_id: str
    points: int
    timestamp: datetime
    event_type: str

# ============================================================================
# LEADERBOARD (SINGLETON)
# ============================================================================

class Leaderboard:
    _instance = None
    _lock = threading.Lock()   # Class-level lock: guards Singleton creation only

    def __new__(cls, *args, **kwargs):
        # BUG FIX: accept *args/**kwargs so Python doesn't complain when __init__
        # has arguments; also safe for subclassing.
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.players: Dict[str, Player] = {}
        self.scores: List[Score] = []

        # Caches: global and regional top-100
        self.global_top_100: List[Tuple[str, int]] = []
        self.regional_tops: Dict[str, List[Tuple[str, int]]] = {}
        self.cache_timestamp = datetime.now()
        self.cache_ttl_seconds = 300  # 5 minutes

        # BUG FIX: RLock instead of Lock.
        # get_global_leaderboard() holds self.lock and calls _recompute_rankings()
        # which also needs self.lock. threading.Lock() deadlocks on re-entry;
        # threading.RLock() allows the same thread to re-acquire.
        self.lock = threading.RLock()
        print("Leaderboard initialized")

    # -------------------------------------------------------------------------
    # PLAYER MANAGEMENT
    # -------------------------------------------------------------------------

    def add_player(self, player_id: str, name: str, region: str):
        with self.lock:
            player = Player(player_id, name, region)
            self.players[player_id] = player
            print(f"  Player registered: {name} ({region})")

    # -------------------------------------------------------------------------
    # SCORE RECORDING
    # -------------------------------------------------------------------------

    def record_score(self, player_id: str, points: int, event_type: str):
        with self.lock:
            if player_id not in self.players:
                return

            player = self.players[player_id]
            player.all_time_score += points
            player.last_update = datetime.now()

            # Record immutable event
            event_id = f"E_{len(self.scores)}"
            score_event = Score(event_id, player_id, points, datetime.now(), event_type)
            self.scores.append(score_event)

            print(f"  {player.name} +{points} pts ({event_type}) -> total: {player.all_time_score}")

    # -------------------------------------------------------------------------
    # CACHE MANAGEMENT
    # -------------------------------------------------------------------------

    def _is_cache_valid(self) -> bool:
        return (datetime.now() - self.cache_timestamp).total_seconds() < self.cache_ttl_seconds

    def _recompute_rankings(self):
        """Recompute top rankings from scratch — called under self.lock (RLock safe)."""
        # Global rankings: sort by score DESC, then timestamp ASC (tiebreak)
        sorted_players = sorted(
            [(pid, p.all_time_score) for pid, p in self.players.items()],
            key=lambda x: (-x[1], self.players[x[0]].last_update)
        )
        self.global_top_100 = sorted_players[:100]

        # Regional rankings
        self.regional_tops = {}
        for region in set(p.region for p in self.players.values()):
            regional = sorted(
                [(pid, p.all_time_score)
                 for pid, p in self.players.items() if p.region == region],
                key=lambda x: (-x[1], self.players[x[0]].last_update)
            )
            self.regional_tops[region] = regional[:100]

        self.cache_timestamp = datetime.now()
        print(f"  Rankings recomputed (cache valid for {self.cache_ttl_seconds}s)")

    # -------------------------------------------------------------------------
    # QUERY METHODS
    # -------------------------------------------------------------------------

    def get_global_leaderboard(self, limit: int = 100) -> List[Tuple[int, str, int]]:
        """Returns: [(rank, player_id, score)]"""
        with self.lock:
            if not self._is_cache_valid():
                self._recompute_rankings()   # Safe: RLock allows re-entry
            return [(rank + 1, pid, score)
                    for rank, (pid, score) in enumerate(self.global_top_100[:limit])]

    def get_regional_leaderboard(self, region: str, limit: int = 100) -> List[Tuple[int, str, int]]:
        """Returns: [(rank, player_id, score)]"""
        with self.lock:
            if not self._is_cache_valid():
                self._recompute_rankings()
            result = []
            if region in self.regional_tops:
                for rank, (pid, score) in enumerate(self.regional_tops[region][:limit], 1):
                    result.append((rank, pid, score))
            return result

    def get_player_rank(self, player_id: str) -> Optional[Tuple[int, int, float]]:
        """Returns: (rank, score, percentile)"""
        with self.lock:
            if not self._is_cache_valid():
                self._recompute_rankings()

            for rank, (pid, score) in enumerate(self.global_top_100, 1):
                if pid == player_id:
                    total = len(self.players)
                    percentile = ((total - rank) / total) * 100 if total else 0.0
                    return (rank, score, percentile)

            # Player exists but not in cached top-100
            if player_id in self.players:
                total = len(self.players)
                return (total + 1, self.players[player_id].all_time_score, 0.0)
            return None

    def get_nearby_players(self, player_id: str, offset: int = 5) -> List[Tuple[int, str, int]]:
        """Returns nearby ranks (player_rank ± offset)."""
        with self.lock:
            if not self._is_cache_valid():
                self._recompute_rankings()

            player_rank = None
            for rank, (pid, _) in enumerate(self.global_top_100, 1):
                if pid == player_id:
                    player_rank = rank
                    break

            if player_rank is None:
                return []

            start = max(0, player_rank - offset - 1)
            end = min(len(self.global_top_100), player_rank + offset)
            result = []
            for rank, (pid, score) in enumerate(self.global_top_100[start:end], start + 1):
                result.append((rank, pid, score))
            return result

    def display_leaderboard(self, limit: int = 10):
        leaderboard = self.get_global_leaderboard(limit)
        print(f"\n  Top {limit} Global Leaderboard:")
        for rank, player_id, score in leaderboard:
            player = self.players[player_id]
            print(f"  {rank:3d}. {player.name:20} {score:10,d} pts ({player.region})")

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_score_updates():
    print("\n" + "="*70)
    print("DEMO 1: SCORE UPDATES & RANKING")
    print("="*70)

    lb = Leaderboard()
    lb.add_player("P1", "Alice", "USA")
    lb.add_player("P2", "Bob", "USA")
    lb.add_player("P3", "Charlie", "USA")

    lb.record_score("P1", 1000, "game_win")
    lb.record_score("P2", 800, "game_win")
    lb.record_score("P3", 500, "game_win")

    lb.display_leaderboard(3)

def demo_2_global_leaderboard():
    print("\n" + "="*70)
    print("DEMO 2: QUERY GLOBAL LEADERBOARD")
    print("="*70)

    lb = Leaderboard()
    for i in range(5):
        lb.add_player(f"P{i}", f"Player{i}", "USA")
        lb.record_score(f"P{i}", (5 - i) * 1000, "game_win")

    leaderboard = lb.get_global_leaderboard(5)
    print(f"\n  Top 5:")
    for rank, pid, score in leaderboard:
        print(f"  Rank {rank}: {lb.players[pid].name} - {score} pts")

def demo_3_player_rank():
    print("\n" + "="*70)
    print("DEMO 3: QUERY PLAYER RANK & PERCENTILE")
    print("="*70)

    lb = Leaderboard()
    for i in range(100):
        lb.add_player(f"P{i}", f"Player{i}", "USA")
        lb.record_score(f"P{i}", (100 - i) * 100, "game_win")

    result = lb.get_player_rank("P50")
    rank, score, percentile = result
    print(f"\n  Player: {lb.players['P50'].name}")
    print(f"  Rank: {rank}")
    print(f"  Score: {score}")
    print(f"  Percentile: {percentile:.2f}%")

def demo_4_nearby_players():
    print("\n" + "="*70)
    print("DEMO 4: NEARBY COMPETITORS")
    print("="*70)

    lb = Leaderboard()
    for i in range(20):
        lb.add_player(f"P{i}", f"Player{i}", "USA")
        lb.record_score(f"P{i}", (20 - i) * 500, "game_win")

    nearby = lb.get_nearby_players("P5", offset=3)
    print(f"\n  Players near P5:")
    for rank, pid, score in nearby:
        print(f"  {rank:2d}. {lb.players[pid].name:15} {score:6d} pts")

def demo_5_regional():
    print("\n" + "="*70)
    print("DEMO 5: REGIONAL LEADERBOARDS")
    print("="*70)

    lb = Leaderboard()
    regions = ["USA", "EU", "ASIA"]

    for region in regions:
        for i in range(5):
            player_id = f"{region}_P{i}"
            lb.add_player(player_id, f"{region}_Player{i}", region)
            lb.record_score(player_id, (5 - i) * 1000, "game_win")

    for region in regions:
        print(f"\n  Top 3 in {region}:")
        leaderboard = lb.get_regional_leaderboard(region, 3)
        for rank, pid, score in leaderboard:
            print(f"  {rank}. {lb.players[pid].name:15} {score} pts")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("LEADERBOARD - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_score_updates()
    demo_2_global_leaderboard()
    demo_3_player_rank()
    demo_4_nearby_players()
    demo_5_regional()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|--------------|------------|
| **add_player** | RLock on instance data | No duplicate registration race |
| **record_score** | RLock on instance data | Atomic score increment + event append |
| **get_global_leaderboard** | RLock (re-entrant) | Safe to call _recompute_rankings under same lock |
| **_recompute_rankings** | Called under RLock | Cache rebuild is atomic; no partial views |
| **Singleton creation** | Class-level Lock (double-checked) | Only one instance created even under contention |

**Concurrency Principles Applied**:
1. RLock allows outer query methods to safely call `_recompute_rankings` without deadlock
2. Singleton uses a separate class-level `Lock` (not the instance `RLock`) — prevents circular dependency at init time
3. Cache is rebuilt atomically under lock — no thread sees a partially-computed leaderboard
4. Notifications (if added) should be dispatched outside the lock to minimize critical section duration

---

## Demo Scenarios

### Demo 1: Score Update & Rank Change
```
- Player John currently rank 500 (score: 50,000)
- John scores 100 points -> new score: 50,100
- Rank recomputed: 2 players passed him
- New rank: 502
- Notification: "Rank dropped 500->502"
```

### Demo 2: Query Leaderboard (Top 100)
```
- User requests top-100 global
- API query: /leaderboard?limit=100&timerange=all-time
- Returns: ranks 1-100 with scores, names, regions
- Latency: 50ms (cached result)
- Display: sorted by score DESC
```

### Demo 3: Regional Leaderboard
```
- Player in USA requests top-100 in USA
- API query: /leaderboard?region=USA&limit=100
- Returns: USA-specific leaderboard
- Player rank: 5,432 out of 2M USA players
- Percentile: 99.73%
```

### Demo 4: Nearby Players
```
- Player at rank 5,000 requests nearby
- API query: /leaderboard/nearby?rank=5000&offset=10
- Returns: ranks 4,990-5,010 (20 players nearby)
- Shows: all scores within 50 points range
- Allows competition/comparison
```

### Demo 5: Season Transition
```
- Season 1 ends: Sept 30
- Leaderboard frozen: top 100 archived
- Season 2 starts: Oct 1
- All scores reset: everyone starts at 0
- Seasonal badges awarded to season 1 top-100
- New leaderboard fresh for competition
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you define leaderboard rank?**

A: Rank = count of players with score strictly greater than current player's score + 1. Example: 50 players above you → rank 51. Ties break by earlier timestamp (who reached the score first gets the better rank).

**Q2: What information do you display?**

A: Player rank (1–10M), player name/avatar, score, region, points earned today, time played. Optional: rating badge (Gold/Silver/Bronze), achievement icons.

**Q3: How frequently should you recompute rankings?**

A: Two approaches: (1) Real-time — recompute immediately (complex, expensive). (2) Batch — recompute every 5–60 minutes (simpler, scalable). Recommendation: batch + cache for consistency and performance.

**Q4: What time windows do you support?**

A: Daily (resets 12 AM UTC), weekly (resets Sundays), monthly (resets 1st), seasonal (3 months), all-time (never resets). Separate leaderboards per window. Player sees all rankings simultaneously.

**Q5: How do you handle region-specific leaderboards?**

A: Partition players by region (geo-IP or account setting). Separate leaderboard per region. Query: top 100 in player's region. Total leaderboards = num_regions × num_time_windows.

### Intermediate Questions

**Q6: How to efficiently query top-100?**

A: Maintain sorted list of top-100 (by score DESC). Data structure: sorted array or Redis ZSET. Query top-100: O(100) = effectively O(1). Update: only reinsert when player score change could affect top-100 membership.

**Q7: How to compute percentile rank?**

A: Percentile = (num_players_below / total_players) × 100. Example: rank 51 out of 10M → (10M − 51) / 10M ≈ 99.99th percentile. Computed on-demand or cached with the ranking.

**Q8: How to show "nearby" competitors?**

A: Store top-1000 rankings. User at rank 500 → show ranks 495–505 (nearby 10). Reduces data transfer and improves performance vs. returning full 10M entries.

**Q9: How to batch process score updates?**

A: Collect score updates in a queue (Redis Stream or Kafka). Every 1 minute: dequeue all, recompute ranks, update cache and DB. Avoids recomputing rankings for each individual update.

**Q10: How to reset leaderboards (seasons)?**

A: At season end — archive current leaderboard (historical data), clear scores, reset ranks, start new season. Players retain seasonal badges but leaderboard resets fresh.

### Advanced Questions

**Q11: How to prevent ranking manipulation?**

A: Score validation: check if score increase is reasonable (e.g., max +100 points per game session). Flag suspicious patterns (rank jump 10M → 1 in one day). Manual review queue before displaying.

**Q12: How to scale to 100 million players?**

A: (1) Partition by region (US, EU, Asia = 33M each). (2) Per region: cache top-1000 globally + top-100 per sub-region. (3) Store full rankings in distributed DB (partition by player ID). (4) Use Redis ZSETs per region for O(log n) updates.

---

## Scaling Q&A

**Q1: Can you handle 10M players with real-time scores?**

A: With batch approach: yes. Batch every 1 minute, recompute rankings in parallel (map-reduce). Bottleneck: storing 10M rankings in memory. Use tiered storage: top-10K in memory, rest in DB.

**Q2: How to handle 100K score updates per second?**

A: Write to message queue (Kafka): 100K msgs/sec. Batch consumer: process 1M events every 10 seconds. Rank recomputation: O(n log n) = O(10M log 10M) ≈ 0.1 seconds on modern hardware.

**Q3: How to keep leaderboard fresh (< 100ms latency)?**

A: Cache top-1000 with TTL 5 minutes. On query: return cached (1ms). On cache miss or expiry: recompute (0.1s), cache new result. Acceptable latency for most use cases.

**Q4: How to handle score ties?**

A: Tiebreaker 1: timestamp (who reached score first). Tiebreaker 2: player_id (lexicographic). Ensures consistent, deterministic ranking. Example: Rank 1 = highest score, earliest timestamp.

**Q5: Can you support country leaderboards for 200 countries?**

A: Yes. 200 separate leaderboards (one per country). Each cached independently. Total memory: 200 × (10K players × 100 bytes) = 200 MB. Reasonable for a dedicated cache tier.

**Q6: How to efficiently update a single player's rank?**

A: Instead of recomputing all 10M: (1) Find player's current rank. (2) Check if new score affects top-1000. If yes: insert into top-1000, remove bottom. If no: update DB only, cache unchanged.

**Q7: How to distribute ranking computation across machines?**

A: Partition players by ID range: Machine 1 handles IDs 1–1M, Machine 2 handles 1M–2M, etc. Each machine computes ranks for its partition. Merge results (distributed sort merge).

**Q8: How to support sub-region leaderboards?**

A: Hierarchical: Global → Country → City → Guild. Cache each level separately. Query city leaderboard: merge city-level + global rank for reference. O(log d) where d = hierarchy depth.

**Q9: How to prevent cache stampede when cache expires?**

A: Probabilistic expiry: instead of TTL = 5 min exactly (all expire at the same time), use TTL = 5 min ± 30 sec (staggered). Prevents thundering herd on simultaneous cache misses.

**Q10: Can you support weighted scores (multiple event types)?**

A: Events: win = 100 pts, kill = 10 pts, death = −5 pts. Total = Σ(event_weight × frequency). Leaderboard ranks by total score. Recompute weights: triggers full leaderboard recomputation.

**Q11: How to handle seasonal resets efficiently?**

A: Archive old season: copy leaderboard table, mark as historic. Create new table for new season. Player sees all seasonal leaderboards (current + archive). Queries filtered by season ID.

**Q12: Can you support spectator mode (follow top-10 updates)?**

A: Broadcast top-10 changes every 1 second via WebSocket. Spectators subscribe to update stream. Expected update frequency: 10–50 rank changes/sec out of 10M — feasible with event streaming.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with all relationships and cardinalities
- [ ] Discuss Singleton pattern with RLock (not Lock) for re-entrant safety
- [ ] Explain cache TTL design and why batch recompute beats per-update recompute
- [ ] Discuss data structure choice: sorted array vs Redis ZSET vs skip list
- [ ] Explain rank formula and tiebreaker (timestamp)
- [ ] Walk through percentile calculation
- [ ] Show regional partitioning strategy
- [ ] Run complete implementation without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Mention thread safety: RLock prevents deadlock on re-entrant calls
- [ ] Discuss trade-offs: cache staleness, memory vs DB, batch vs real-time

---

**Ready for interview? Climb the leaderboard!**
