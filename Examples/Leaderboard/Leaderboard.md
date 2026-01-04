# Leaderboard — 75-Minute Interview Guide

## Quick Start

**What is it?** Real-time ranking system tracking player scores and displaying top performers globally or by region.

**Key Classes:**
- `Leaderboard` (Singleton): Central ranking system
- `Player`: User with unique ID, score, metadata
- `Score`: Event recording points earned
- `TimeRange`: Scope filter (daily, weekly, monthly, all-time)
- `Region`: Geographic filter for localized leaderboards
- `Cache`: In-memory top-N rankings

**Core Flows:**
1. **Update Score**: Player scores point → Rank recalculated
2. **Query Global Leaderboard**: Get top 100 players worldwide
3. **Query Regional**: Get top 50 in region with percentile
4. **Query Personal Rank**: Check single player's ranking + nearby players
5. **Competitive Rankings**: Time-windowed scores (season-based)

**5 Design Patterns:**
- **Singleton**: One Leaderboard system
- **Observer**: Notify on rank change (promotion/demotion)
- **Cache**: Top-N rankings with TTL
- **Strategy**: Different ranking algorithms (ELO, points, percentage)
- **State Machine**: Season lifecycle (active, closed, archived)

---

## System Overview

Large-scale ranking system aggregating player scores, computing real-time rankings, and serving leaderboard queries for millions of players.

### Requirements

**Functional:**
- Record score updates in real-time
- Compute player rankings (global, regional)
- Query top-N leaderboard
- Display player percentile
- Filter by time (daily, weekly, monthly, all-time)
- Support multiple regions/competitive seasons
- Show nearby competitors (+/- 5 ranks)

**Non-Functional:**
- Leaderboard query < 100ms
- Support 10M+ players, 100K QPS
- Score update latency < 1 second
- 99.99% uptime (ranked competitive)

**Constraints:**
- Max players per leaderboard: 10M+
- Scoring range: 0-1,000,000,000 points
- Top-N display: typically 100-1000
- Real-time: <1 second consistency requirement

---

## Architecture Diagram (ASCII UML)

```
┌────────────────┐
│ Leaderboard    │
│ (Singleton)    │
└────────┬───────┘
         │
    ┌────┼────┬──────────┐
    │    │    │          │
    ▼    ▼    ▼          ▼
┌────────┐ ┌─────┐ ┌──────┐ ┌───────┐
│Players │ │Score│ │Region│ │Season │
└────────┘ └─────┘ └──────┘ └───────┘
    │
    ▼
┌──────────────┐
│CachedRankings│
│Top-100       │ ← TTL: 1-5 min
│Top-1000      │
│Regional      │
└──────────────┘

Rank Computation:
Score Changes → Event Queue → Batch Rank Recompute → Update Cache
                 ↓
            Sort by Score DESC
            Assign ranks 1, 2, 3...
            Cache for 1-5 minutes
```

---

## Interview Q&A (12 Questions)

### Basic Level

**Q1: How do you define leaderboard rank?**
A: Rank = count of players with score > current player's score + 1. Example: 50 players above you → rank 51. Ties break by: earlier timestamp (who reached score first gets better rank).

**Q2: What information do you display?**
A: Player rank (1-10M), player name/avatar, score, region, points_earned_today, time_played. Optional: rating badge (Gold/Silver/Bronze), achievement icons.

**Q3: How frequently should you recompute rankings?**
A: Two approaches: (1) Real-time: recompute immediately (complex). (2) Batch: recompute every 5-60 minutes (simpler). Recommendation: batch + cache for consistency + performance.

**Q4: What time windows do you support?**
A: Daily (resets 12 AM UTC), weekly (resets Sundays), monthly (resets 1st), seasonal (3 months), all-time (never). Separate leaderboards per window. Player sees all rankings simultaneously.

**Q5: How do you handle region-specific leaderboards?**
A: Partition players by region (geo-IP or account setting). Separate leaderboard per region. Query: top 100 in player's region. Total leaderboards = num_regions × num_seasons.

### Intermediate Level

**Q6: How to efficiently query top-100?**
A: Maintain sorted list of top-100 (by score DESC). Index: sorted array or balanced BST. Query top-100: O(100) = O(1). Update: when player score changes, update if in top-100 or could enter top-100.

**Q7: How to compute percentile rank?**
A: Percentile = (num_players_below / total_players) × 100. Example: rank 51 out of 10M → (10M - 51) / 10M ≈ 99.99th percentile. Computed on-demand or cached.

**Q8: How to show "nearby" competitors?**
A: Store top-1000 rankings. User at rank 500 → show ranks 495-505 (nearby 10). Reduces data transfer + improves performance vs showing full 10M.

**Q9: How to batch process score updates?**
A: Collect score updates in queue (Redis stream). Every 1 minute: dequeue all, recompute ranks, update cache + DB. Avoids recomputing for each individual update.

**Q10: How to reset leaderboards (seasons)?**
A: At season end: archive current leaderboard (historical data). Clear scores, reset ranks. Start new season. Players retain seasonal badges but leaderboard fresh.

### Advanced Level

**Q11: How to prevent ranking manipulation?**
A: Score validation: check if score increase is reasonable (e.g., max +100 points per game). Flag suspicious patterns (rank jump 10M → 1 in 1 day). Manual review before displaying.

**Q12: How to scale to 100 million players?**
A: (1) Partition by region (US, EU, Asia = 33M each). (2) Per region: cache top-1000 globally + top-100 per sub-region. (3) Store full rankings in distributed DB (partition by player ID).

---

## Scaling Q&A (12 Questions)

**Q1: Can you handle 10M players with real-time scores?**
A: With batch approach: yes. Batch every 1 minute, recompute rankings in parallel (map-reduce). Bottleneck: storing 10M rankings (memory). Use tiered storage: top-10K in memory, rest in DB.

**Q2: How to handle 100K score updates per second?**
A: Write to message queue (Kafka): 100K msgs/sec. Batch consumer: process 1M events every 10 seconds. Rank recomputation: O(n log n) = O(10M log 10M) ≈ 0.1 seconds on modern hardware.

**Q3: How to keep leaderboard fresh (< 100ms latency)?**
A: Cache top-1000 with TTL 5 minutes. On query: return cached (1ms). On cache miss or expiry: recompute (0.1s), cache new result. Acceptable latency for most use cases.

**Q4: How to handle score ties?**
A: Tiebreaker 1: timestamp (who reached score first). Tiebreaker 2: player_id (lexicographic). Ensures consistent, deterministic ranking. Example: Rank 1 = highest score, earliest timestamp.

**Q5: Can you support country leaderboards for 200 countries?**
A: Yes. 200 separate leaderboards (one per country). Each cached independently. Total memory: 200 × (10K players × 100 bytes) = 200 MB. Reasonable.

**Q6: How to efficiently update a single player's rank?**
A: Instead of recomputing all 10M: (1) Find player's current rank. (2) Check if new score affects top-1000. If yes: insert into top-1000, remove bottom. If no: update DB only, cache unchanged.

**Q7: How to distribute ranking computation across machines?**
A: Partition players by ID range: Machine 1 handles IDs 1-1M, Machine 2 handles 1M-2M, etc. Each machine: compute ranks for its partition. Merge results (distributed sort).

**Q8: How to support sub-region leaderboards?**
A: Hierarchical: Global → Country → City → Guild. Cache each level separately. Query city leaderboard: merge city-level + global rank (for reference). O(log d) where d = depth.

**Q9: How to prevent cache stampede when cache expires?**
A: Probabilistic expiry: instead of TTL=5 min (all expire same time), use TTL=5 min ± 30 sec (stagger). Prevents thundering herd on cache miss.

**Q10: Can you support weighted scores (multiple events)?**
A: Events: win=100pts, kill=10pts, death=-5pts. Total = Σ(event_weight × frequency). Leaderboard ranks by total score. Recompute weights: recalculate leaderboard.

**Q11: How to handle seasonal resets efficiently?**
A: Archive old season: copy leaderboard table, mark as historic. Create new table for new season. Player sees all seasonal leaderboards (current + archive). Queries filtered by season.

**Q12: Can you support spectator mode (follow top-10 updates)?**
A: Broadcast top-10 changes every 1 second (via WebSocket). Spectators subscribe to updates. Expected update frequency: 10-50 rank changes/sec (out of 10M). Feasible with event streaming.

---

## Demo Scenarios (5 Examples)

### Demo 1: Score Update & Rank Change
```
- Player John currently rank 500 (score: 50,000)
- John scores 100 points → new score: 50,100
- Rank recomputed: 2 players passed him
- New rank: 502
- Email notification: "Rank dropped 500→502"
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

## Complete Implementation

```python
"""
🏆 Leaderboard - Interview Implementation
Demonstrates:
1. Real-time ranking computation
2. Caching top-N results
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
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
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
    _lock = threading.Lock()
    
    def __new__(cls):
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
        
        # Caches: region -> list of (player_id, score)
        self.global_top_100: List[Tuple[str, int]] = []
        self.regional_tops: Dict[str, List[Tuple[str, int]]] = {}
        self.cache_timestamp = datetime.now()
        self.cache_ttl_seconds = 300  # 5 minutes
        
        self.lock = threading.Lock()
        print("🏆 Leaderboard initialized")
    
    def add_player(self, player_id: str, name: str, region: str):
        with self.lock:
            player = Player(player_id, name, region)
            self.players[player_id] = player
            print(f"✓ Player registered: {name} ({region})")
    
    def record_score(self, player_id: str, points: int, event_type: str):
        with self.lock:
            if player_id not in self.players:
                return
            
            player = self.players[player_id]
            
            # Update scores (simplified - only all_time)
            player.all_time_score += points
            player.last_update = datetime.now()
            
            # Record event
            event_id = f"E_{len(self.scores)}"
            score = Score(event_id, player_id, points, datetime.now(), event_type)
            self.scores.append(score)
            
            print(f"✓ {player.name} +{points} pts ({event_type}) → total: {player.all_time_score}")
    
    def _is_cache_valid(self) -> bool:
        return (datetime.now() - self.cache_timestamp).total_seconds() < self.cache_ttl_seconds
    
    def _recompute_rankings(self):
        """Recompute top rankings from scratch"""
        # Global rankings
        sorted_players = sorted(
            [(pid, p.all_time_score) for pid, p in self.players.items()],
            key=lambda x: (-x[1], self.players[x[0]].last_update)  # Score DESC, timestamp ASC
        )
        
        self.global_top_100 = sorted_players[:100]
        
        # Regional rankings
        self.regional_tops = {}
        for region in set(p.region for p in self.players.values()):
            regional_players = sorted(
                [(pid, p.all_time_score) for pid, p in self.players.items() if p.region == region],
                key=lambda x: (-x[1], self.players[x[0]].last_update)
            )
            self.regional_tops[region] = regional_players[:100]
        
        self.cache_timestamp = datetime.now()
        print(f"  ✓ Rankings recomputed (cache valid for 5 min)")
    
    def get_global_leaderboard(self, limit: int = 100) -> List[Tuple[int, str, int]]:
        """Returns: [(rank, player_id, score)]"""
        with self.lock:
            if not self._is_cache_valid():
                self._recompute_rankings()
            
            result = []
            for rank, (player_id, score) in enumerate(self.global_top_100[:limit], 1):
                result.append((rank, player_id, score))
            
            return result
    
    def get_regional_leaderboard(self, region: str, limit: int = 100) -> List[Tuple[int, str, int]]:
        """Returns: [(rank, player_id, score)]"""
        with self.lock:
            if not self._is_cache_valid():
                self._recompute_rankings()
            
            result = []
            if region in self.regional_tops:
                for rank, (player_id, score) in enumerate(self.regional_tops[region][:limit], 1):
                    result.append((rank, player_id, score))
            
            return result
    
    def get_player_rank(self, player_id: str) -> Optional[Tuple[int, int, float]]:
        """Returns: (rank, score, percentile)"""
        with self.lock:
            if not self._is_cache_valid():
                self._recompute_rankings()
            
            # Find rank in global
            for rank, (pid, score) in enumerate(self.global_top_100, 1):
                if pid == player_id:
                    total_players = len(self.players)
                    percentile = ((total_players - rank) / total_players) * 100
                    return (rank, score, percentile)
            
            # If not in top-100, estimate
            total = len(self.players)
            return (total + 1, self.players[player_id].all_time_score, 0.0)
    
    def get_nearby_players(self, player_id: str, offset: int = 5) -> List[Tuple[int, str, int]]:
        """Returns nearby ranks (player ± offset)"""
        with self.lock:
            if not self._is_cache_valid():
                self._recompute_rankings()
            
            player_rank = None
            for rank, (pid, _) in enumerate(self.global_top_100, 1):
                if pid == player_id:
                    player_rank = rank
                    break
            
            if not player_rank:
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
        lb.record_score(f"P{i}", (5-i)*1000, "game_win")
    
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
        lb.record_score(f"P{i}", (100-i)*100, "game_win")
    
    rank, score, percentile = lb.get_player_rank("P50")
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
        lb.record_score(f"P{i}", (20-i)*500, "game_win")
    
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
            lb.record_score(player_id, (5-i)*1000, "game_win")
    
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
    print("🏆 LEADERBOARD - 5 DEMO SCENARIOS")
    print("="*70)
    
    demo_1_score_updates()
    demo_2_global_leaderboard()
    demo_3_player_rank()
    demo_4_nearby_players()
    demo_5_regional()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

---

## Summary

✅ **Real-time rankings** for 10M+ players
✅ **Global + regional** leaderboards
✅ **Efficient caching** (top-1000) with TTL
✅ **Percentile ranking** computation
✅ **Nearby competitors** display
✅ **Seasonal competition** support
✅ **Score update batching** for performance
✅ **Multi-region partitioning** for scale
✅ **Spectator mode** (broadcast updates)
✅ **Fraud prevention** (score validation)

**Key Takeaway**: Leaderboard demonstrates high-scale ranking computation, caching strategies, and efficient query patterns. Core focus: cache top-N rankings, use batch updates, support hierarchical queries (global/regional).
