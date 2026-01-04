# Parking Lot — 75-Minute Interview Guide

Single-lot parking system with multiple spot/vehicle types, ticketing, payments, and live display updates. Scope: one lot, in-memory state, simple payments simulation.

## Timeline (75 minutes)
| Time | Phase | Output |
|------|-------|--------|
| 0–5 | Requirements | Spot/vehicle types, capacity, billing rules |
| 5–15 | Architecture | Patterns + class responsibilities |
| 15–35 | Core Entities | Vehicle/Spot hierarchy, Ticket, Payment |
| 35–55 | Logic | Assign spot, issue ticket, process exit/payment |
| 55–70 | Integration | DisplayBoard observer, stats, demo flows |
| 70–75 | Q&A | Trade-offs, scaling story |

## Requirements & Assumptions
- Spot types: Compact, Large, Handicapped, Motorcycle.  
- Vehicle types: Car, Van, Truck, Motorcycle.  
- Capacity: configurable; single lot; payments simulated (cash/card).  
- Flow: enter → assign spot → issue ticket → exit → pay → free spot.  
- Observer for live display; Strategy hook for spot assignment.

## Design Patterns
- **Singleton**: `ParkingLot` (single instance manages state).  
- **Strategy**: Spot selection algorithm (e.g., nearest, level-aware).  
- **Observer**: `DisplayBoard` subscribes to occupancy changes.  
- **Factory**: Vehicle/payment creation helpers.  
- **State**: Ticket lifecycle (ACTIVE → PAID/LOST).  
- **Decorator (optional)**: Premium/VIP features layered onto spots or tickets.

## Architecture Sketch
```
EntranceGate → ParkingLot (Singleton) → buckets per SpotType
                               │
                               ├─ issue_ticket(vehicle) → Ticket
                               ├─ assign_spot(vehicle) using Strategy
                               ├─ exit(ticket, payment) → free spot, update revenue
                               └─ notify observers (DisplayBoard) on changes

Buckets: {SpotType: [available spots]} for O(1) assign/free
Payments: strategy/handlers (CashPayment, CardPayment)
```

## UML Class Diagram (text)
```
┌───────────────────────┐           ┌────────────────────┐
│      ParkingLot       │ (Singleton)    │ DisplayBoard (Observer)
├───────────────────────┤           └────────────────────┘
│- spots_by_type: dict  │                 ▲
│- tickets: dict        │                 │ observes
│- strategy: SpotStrategy│                │
│- observers: list      │                 │
├───────────────────────┤                 │
│+ assign_spot(vehicle) │                 │
│+ issue_ticket(vehicle)│                 │
│+ process_exit(ticket) │                 │
│+ notify_observers()   │-----------------┘
└──────────┬────────────┘
           │ uses
           ▼
    ┌──────────────┐       implements        ┌────────────────────┐
    │ SpotStrategy │<----------------------- │ DefaultSpotStrategy │
    └──────────────┘                         └────────────────────┘

┌──────────────┐    has-a    ┌──────────────┐
│    Ticket    │------------>│ Payment      │◄─┐
├──────────────┤             ├──────────────┤  │implements
│ status/state │             │ amount, time │  │
└──────────────┘             └──────────────┘  │
                                               │
                               ┌─────────────────────────┐
                               │ CashPayment / CardPayment│
                               └─────────────────────────┘

┌──────────────┐   inherits   ┌──────────────┐
│   Vehicle    │<------------ │ Car/Van/Truck│ ...
└──────────────┘              └──────────────┘

┌──────────────┐   inherits   ┌──────────────┐
│  ParkingSpot │<------------ │ CompactSpot… │ ...
└──────────────┘              └──────────────┘
```

## Core Model
- **Vehicle**: type, license; subclasses per vehicle type.  
- **ParkingSpot**: id, type, allowed vehicles, occupied flag.  
- **Ticket**: id, vehicle, spot, entry/exit time, fee, status.  
- **Payment**: amount, timestamp, method.  
- **DisplayBoard (Observer)**: renders available/occupied counts.  
- **SpotStrategy**: picks next spot from buckets.

## Flow & Invariants
1) On entry: find compatible spot via strategy; mark occupied; issue ticket.  
2) On exit: compute fee; process payment; free spot; notify observers.  
3) Buckets per SpotType give O(1) allocate/free.  
4) Ticket state transitions are explicit (ACTIVE → PAID/LOST).

## Demo Scenarios (examples)
1. Basic entry/exit for car, show ticket, free spot.  
2. Mixed vehicles: car→compact, truck→large, bike→motorcycle.  
3. Lot full → reject and message.  
4. Payment flows: cash vs card; ticket state update.  
5. Stats: available by type, revenue, utilization.

Run demos: `python3 "Parking Lot.md"` (or copy code to a `.py` file).

## Scaling & Trade-offs (Q&A)
- **Large lot / multi-level?** Add level info to spots; strategy chooses nearest level; shard buckets by level.  
- **High throughput?** Keep buckets in memory; use locks/atomic ops per bucket; batch display updates; async payments.  
- **Consistency?** Guard assign/free with mutex or DB row locks; idempotent exit handling; prevent double-free/double-assign.  
- **Extensibility?** Strategy per vehicle class, EV charging decorator, pricing strategy per duration.  
- **Data persistence?** Periodic snapshots of occupancy and tickets; append-only event log for reconciliation.

## Compact Code
```python
"""Simplified Parking Lot with Strategy + Observer + State"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional
import time

class VehicleType(Enum):
    CAR = auto()
    VAN = auto()
    TRUCK = auto()
    MOTORCYCLE = auto()

class SpotType(Enum):
    COMPACT = auto()
    LARGE = auto()
    HANDICAPPED = auto()
    MOTORCYCLE = auto()

class TicketStatus(Enum):
    ACTIVE = auto()
    PAID = auto()
    LOST = auto()

class PaymentMethod(Enum):
    CASH = auto()
    CARD = auto()

@dataclass
class Vehicle:
    plate: str
    vehicle_type: VehicleType

@dataclass
class ParkingSpot:
    spot_id: str
    spot_type: SpotType
    occupied: bool = False
    vehicle: Optional[Vehicle] = None

    def can_fit(self, vehicle: Vehicle) -> bool:
        if self.occupied:
            return False
        if self.spot_type == SpotType.MOTORCYCLE:
            return vehicle.vehicle_type == VehicleType.MOTORCYCLE
        if self.spot_type == SpotType.HANDICAPPED:
            return vehicle.vehicle_type in {VehicleType.CAR, VehicleType.VAN, VehicleType.MOTORCYCLE}
        if self.spot_type == SpotType.COMPACT:
            return vehicle.vehicle_type in {VehicleType.CAR, VehicleType.VAN, VehicleType.MOTORCYCLE}
        return True  # LARGE fits all

    def park(self, vehicle: Vehicle):
        if not self.can_fit(vehicle):
            raise ValueError("Spot not available")
        self.occupied = True
        self.vehicle = vehicle

    def free(self):
        self.occupied = False
        self.vehicle = None

@dataclass
class Ticket:
    ticket_id: str
    vehicle: Vehicle
    spot: ParkingSpot
    entry_time: float
    exit_time: Optional[float] = None
    amount: float = 0.0
    status: TicketStatus = TicketStatus.ACTIVE

@dataclass
class Payment:
    amount: float
    method: PaymentMethod
    paid_at: float

class SpotStrategy:
    def select_spot(self, vehicle: Vehicle, buckets: Dict[SpotType, List[ParkingSpot]]) -> Optional[ParkingSpot]:
        raise NotImplementedError

class DefaultSpotStrategy(SpotStrategy):
    ORDER = [SpotType.HANDICAPPED, SpotType.COMPACT, SpotType.LARGE, SpotType.MOTORCYCLE]
    def select_spot(self, vehicle: Vehicle, buckets: Dict[SpotType, List[ParkingSpot]]) -> Optional[ParkingSpot]:
        for st in self.ORDER:
            for spot in buckets.get(st, []):
                if spot.can_fit(vehicle):
                    return spot
        return None

class Observer:
    def update(self, event: str, payload: dict):
        pass

class DisplayBoard(Observer):
    def update(self, event: str, payload: dict):
        if event == "spot_change":
            print(f"[DISPLAY] {payload['available']} spots available")
        if event == "payment":
            print(f"[DISPLAY] Ticket {payload['ticket_id']} paid ${payload['amount']:.2f}")

class ParkingLot:
    _instance: Optional["ParkingLot"] = None
    def __init__(self):
        self.buckets: Dict[SpotType, List[ParkingSpot]] = {st: [] for st in SpotType}
        self.tickets: Dict[str, Ticket] = {}
        self.strategy: SpotStrategy = DefaultSpotStrategy()
        self.observers: List[Observer] = []
        self.ticket_seq = 0

    @classmethod
    def instance(cls) -> "ParkingLot":
        if cls._instance is None:
            cls._instance = ParkingLot()
        return cls._instance

    def add_observer(self, obs: Observer):
        self.observers.append(obs)

    def notify(self, event: str, payload: dict):
        for obs in self.observers:
            obs.update(event, payload)

    def add_spot(self, spot: ParkingSpot):
        self.buckets[spot.spot_type].append(spot)

    def issue_ticket(self, vehicle: Vehicle) -> Optional[Ticket]:
        spot = self.strategy.select_spot(vehicle, self.buckets)
        if not spot:
            print("No spot available")
            return None
        spot.park(vehicle)
        self.ticket_seq += 1
        ticket_id = f"T{self.ticket_seq:04d}"
        ticket = Ticket(ticket_id, vehicle, spot, time.time())
        self.tickets[ticket_id] = ticket
        self.notify("spot_change", {"available": self.available_spots_count()})
        return ticket

    def process_exit(self, ticket_id: str, method: PaymentMethod, rate_per_hour: float = 5.0) -> bool:
        ticket = self.tickets.get(ticket_id)
        if not ticket or ticket.status != TicketStatus.ACTIVE:
            return False
        ticket.exit_time = time.time()
        hours = max(1, (ticket.exit_time - ticket.entry_time) / 3600.0)
        ticket.amount = rate_per_hour * hours
        payment = Payment(ticket.amount, method, ticket.exit_time)
        ticket.status = TicketStatus.PAID
        ticket.spot.free()
        self.notify("payment", {"ticket_id": ticket.ticket_id, "amount": ticket.amount, "method": method.name})
        self.notify("spot_change", {"available": self.available_spots_count()})
        return True

    def available_spots_count(self) -> int:
        return sum(1 for bucket in self.buckets.values() for spot in bucket if not spot.occupied)

# ---------------------- Demo ----------------------
if __name__ == "__main__":
    lot = ParkingLot.instance()
    lot.add_observer(DisplayBoard())
    lot.add_spot(ParkingSpot("C1", SpotType.COMPACT))
    lot.add_spot(ParkingSpot("L1", SpotType.LARGE))
    lot.add_spot(ParkingSpot("M1", SpotType.MOTORCYCLE))

    t1 = lot.issue_ticket(Vehicle("ABC123", VehicleType.CAR))
    t2 = lot.issue_ticket(Vehicle("XYZ999", VehicleType.MOTORCYCLE))
    if t1:
        lot.process_exit(t1.ticket_id, PaymentMethod.CARD)
    if t2:
        lot.process_exit(t2.ticket_id, PaymentMethod.CASH)
    print(f"Available spots: {lot.available_spots_count()}")
```

## Key Takeaways
- Bucket spots by type for O(1) assign/free; guard state transitions.  
- Decouple UI via Observer; make spot selection pluggable via Strategy.  
- Scaling: shard by level/zone, add locks/transactions for consistency, async payments/display updates, and snapshot state for durability.***
