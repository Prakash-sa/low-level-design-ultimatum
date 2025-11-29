"""Stack Overflow - Interview Compact Implementation
Design Patterns: Singleton | Strategy (Reputation) | Observer | State | Factory
Demonstrates 5 scenarios analogous to Airline example.
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

# ============================================================================
# ENUMERATIONS & CONSTANTS
# ============================================================================

class QuestionStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"

class VoteValue(Enum):
    UP = 1
    DOWN = -1

REP_Q_UP = 10
REP_A_UP = 15
REP_ACCEPT = 30
REP_DOWN_AUTHOR = -2
REP_DOWN_VOTER = -1

# ============================================================================
# CORE DOMAIN ENTITIES
# ============================================================================

class User:
    def __init__(self, user_id: str, name: str):
        self.id = user_id
        self.name = name
        self.reputation = 0
        self.questions: List['Question'] = []
        self.answers: List['Answer'] = []
    def __repr__(self):
        return f"User(id={self.id}, rep={self.reputation})"

class Question:
    def __init__(self, qid: str, title: str, body: str, author: User, tags: List[str]):
        self.id = qid
        self.title = title
        self.body = body
        self.author = author
        self.tags = [t.lower() for t in tags]
        self.answers: List['Answer'] = []
        self.votes = 0
        self.accepted_answer_id: Optional[str] = None
        self.status = QuestionStatus.OPEN
        self.created_at = datetime.now()
    def add_answer(self, answer: 'Answer'):
        self.answers.append(answer)
    def __repr__(self):
        return f"Question({self.id}, votes={self.votes}, answers={len(self.answers)})"

class Answer:
    def __init__(self, aid: str, body: str, author: User, question: Question):
        self.id = aid
        self.body = body
        self.author = author
        self.question = question
        self.votes = 0
        self.accepted = False
        self.created_at = datetime.now()
    def __repr__(self):
        return f"Answer({self.id}, votes={self.votes}, accepted={self.accepted})"

class Vote:
    def __init__(self, vid: str, user: User, target_type: str, target_id: str, value: VoteValue):
        self.id = vid
        self.user = user
        self.target_type = target_type  # 'question' or 'answer'
        self.target_id = target_id
        self.value = value
        self.created_at = datetime.now()

# ============================================================================
# REPUTATION STRATEGY (Strategy Pattern)
# ============================================================================

class ReputationStrategy(ABC):
    @abstractmethod
    def apply_vote(self, system: 'StackOverflowSystem', vote: Vote):
        pass
    @abstractmethod
    def apply_accept(self, system: 'StackOverflowSystem', question: Question, answer: Answer):
        pass

class BasicReputationStrategy(ReputationStrategy):
    def apply_vote(self, system: 'StackOverflowSystem', vote: Vote):
        if vote.target_type == "question":
            q = system.questions.get(vote.target_id)
            if not q: return
            if vote.value == VoteValue.UP:
                q.author.reputation += REP_Q_UP
            else:
                q.author.reputation += REP_DOWN_AUTHOR
                vote.user.reputation += REP_DOWN_VOTER
        else:
            a = system.answers.get(vote.target_id)
            if not a: return
            if vote.value == VoteValue.UP:
                a.author.reputation += REP_A_UP
            else:
                a.author.reputation += REP_DOWN_AUTHOR
                vote.user.reputation += REP_DOWN_VOTER
    def apply_accept(self, system: 'StackOverflowSystem', question: Question, answer: Answer):
        answer.author.reputation += REP_ACCEPT

# ============================================================================
# OBSERVER PATTERN
# ============================================================================

class Observer(ABC):
    @abstractmethod
    def update(self, event: str, payload: Dict):
        pass

class ConsoleObserver(Observer):
    def update(self, event: str, payload: Dict):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {event.upper():16} | {payload}")

# ============================================================================
# SINGLETON SYSTEM CONTROLLER
# ============================================================================

class StackOverflowSystem:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self):
        if getattr(self, '_initialized', False): return
        self.users: Dict[str, User] = {}
        self.questions: Dict[str, Question] = {}
        self.answers: Dict[str, Answer] = {}
        self.votes: Dict[str, Vote] = {}
        self.observers: List[Observer] = []
        self.reputation_strategy: ReputationStrategy = BasicReputationStrategy()
        self._initialized = True
    def add_observer(self, obs: Observer):
        self.observers.append(obs)
    def _notify(self, event: str, payload: Dict):
        for o in self.observers: o.update(event, payload)
    def create_user(self, name: str) -> User:
        uid = f"U{len(self.users)+1}"; u = User(uid, name); self.users[uid] = u
        self._notify("user_created", {"user_id": uid, "name": name})
        return u
    def ask_question(self, user_id: str, title: str, body: str, tags: List[str]) -> Optional[Question]:
        user = self.users.get(user_id)
        if not user: return None
        qid = f"Q{len(self.questions)+1}"; q = Question(qid, title, body, user, tags)
        user.questions.append(q); self.questions[qid] = q
        self._notify("question_posted", {"qid": qid, "author": user.name, "title": title})
        return q
    def answer_question(self, user_id: str, question_id: str, body: str) -> Optional[Answer]:
        user = self.users.get(user_id); q = self.questions.get(question_id)
        if not user or not q or q.status != QuestionStatus.OPEN: return None
        aid = f"A{len(self.answers)+1}"; a = Answer(aid, body, user, q); q.add_answer(a)
        user.answers.append(a); self.answers[aid] = a
        self._notify("answer_posted", {"aid": aid, "qid": question_id, "author": user.name})
        return a
    def vote(self, user_id: str, target_type: str, target_id: str, up: bool = True) -> Optional[Vote]:
        voter = self.users.get(user_id)
        if not voter: return None
        if target_type == "question" and target_id not in self.questions: return None
        if target_type == "answer" and target_id not in self.answers: return None
        vid = f"V{len(self.votes)+1}"; value = VoteValue.UP if up else VoteValue.DOWN
        v = Vote(vid, voter, target_type, target_id, value); self.votes[vid] = v
        if target_type == "question": self.questions[target_id].votes += value.value
        else: self.answers[target_id].votes += value.value
        self.reputation_strategy.apply_vote(self, v)
        self._notify("vote_cast", {"vid": vid, "target": target_id, "type": target_type, "value": value.name})
        return v
    def accept_answer(self, user_id: str, question_id: str, answer_id: str) -> bool:
        q = self.questions.get(question_id); a = self.answers.get(answer_id)
        if not q or not a: return False
        if q.author.id != user_id or q.accepted_answer_id is not None or a.question.id != q.id: return False
        q.accepted_answer_id = answer_id; a.accepted = True
        self.reputation_strategy.apply_accept(self, q, a)
        self._notify("answer_accepted", {"qid": question_id, "aid": answer_id})
        return True
    def search(self, keyword: str) -> List[Question]:
        k = keyword.lower()
        return [q for q in self.questions.values() if k in q.title.lower() or k in q.body.lower()]
    def summary(self) -> Dict[str, int]:
        return {
            "users": len(self.users),
            "questions": len(self.questions),
            "answers": len(self.answers),
            "votes": len(self.votes)
        }

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_setup(system: StackOverflowSystem):
    print("\n" + "="*70); print("DEMO 1: System Setup & Question Posting"); print("="*70)
    system.observers.clear(); system.add_observer(ConsoleObserver())
    u1 = system.create_user("Alice"); u2 = system.create_user("Bob")
    q = system.ask_question(u1.id, "How to reverse a list in Python?", "Looking for idiomatic ways.", ["python", "list"])
    print(f"✅ Users: {u1.id},{u2.id} | Question: {q.id} -> {q.title}")
    return u1, u2, q

def demo_2_answer_flow(system: StackOverflowSystem, u1: User, u2: User, q: Question):
    print("\n" + "="*70); print("DEMO 2: Answer Flow"); print("="*70)
    a1 = system.answer_question(u2.id, q.id, "Use slicing: lst[::-1]")
    a2 = system.answer_question(u1.id, q.id, "Use reversed() and list() for iterator.")
    print(f"✅ Answers posted: {[a.id for a in q.answers]}")
    return a1, a2

def demo_3_voting(system: StackOverflowSystem, q: Question, a1: Answer, a2: Answer, u1: User, u2: User):
    print("\n" + "="*70); print("DEMO 3: Voting & Reputation"); print("="*70)
    system.vote(u2.id, "question", q.id, up=True)   # Bob upvotes Alice's question
    system.vote(u1.id, "answer", a1.id, up=True)     # Alice upvotes Bob's answer
    system.vote(u2.id, "answer", a2.id, up=False)    # Bob downvotes Alice's answer
    print(f"✅ Reputations -> Alice: {u1.reputation}, Bob: {u2.reputation}")

def demo_4_accept(system: StackOverflowSystem, u1: User, q: Question, a1: Answer):
    print("\n" + "="*70); print("DEMO 4: Accept Answer"); print("="*70)
    ok = system.accept_answer(u1.id, q.id, a1.id)
    print(f"✅ Accepted: {ok} | Accepted Answer ID: {q.accepted_answer_id} | Bob Rep: {a1.author.reputation}")

def demo_5_search_summary(system: StackOverflowSystem):
    print("\n" + "="*70); print("DEMO 5: Search & Summary"); print("="*70)
    results = system.search("reverse")
    print(f"✅ Search 'reverse' results: {[q.id for q in results]}")
    print("[SUMMARY]")
    print(system.summary())

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("STACK OVERFLOW - 75 MINUTE INTERVIEW DEMOS")
    print("Design Patterns: Singleton | Strategy | Observer | State | Factory")
    print("="*70)
    sys = StackOverflowSystem()
    try:
        u1, u2, q = demo_1_setup(sys)
        a1, a2 = demo_2_answer_flow(sys, u1, u2, q)
        demo_3_voting(sys, q, a1, a2, u1, u2)
        demo_4_accept(sys, u1, q, a1)
        demo_5_search_summary(sys)
        print("\n" + "="*70)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("Key Takeaways:")
        print(" • Reputation centralized (Strategy) allows easy rule changes")
        print(" • Observer decouples side-effects from core logic")
        print(" • Single accepted answer invariant enforced")
        print(" • Simple search stub discussable upgrade path")
    except Exception as e:
        print(f"❌ Error during demos: {e}")
        import traceback; traceback.print_exc()
