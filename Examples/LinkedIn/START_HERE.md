# 💼 LinkedIn - Quick Start Guide

## ⏱️ 75-Minute Interview Breakdown
| Time | What to Do | Duration |
|------|-----------|----------|
| 0-10 min | Requirements & Architecture | 10 min |
| 10-30 min | Core Entities & Classes | 20 min |
| 30-50 min | Patterns & Business Logic | 20 min |
| 50-70 min | System Integration | 20 min |
| 70-75 min | Demos & Q&A | 5 min |

## 📋 Core Entities (6 Main Classes)
| Entity | Key Attributes | Key Methods |
|--------|---------------|-------------|
| **User** | user_id, name, headline, skills, experience | add_skill(), add_experience() |
| **Connection** | from_user, to_user, status, timestamp | accept(), reject() |
| **Post** | post_id, author, content, likes, comments | add_like(), add_comment() |
| **Job** | job_id, company, title, requirements | apply(), close() |
| **Message** | message_id, sender, receiver, content | mark_read(), reply() |
| **Company** | company_id, name, industry, followers | add_job(), follow() |

## 🎨 Design Patterns (5 Patterns)
| Pattern | Usage | Example |
|---------|-------|---------|
| **Singleton** | LinkedIn system instance | `LinkedInSystem.get_instance()` |
| **Observer** | Feed updates & notifications | User posts → followers notified |
| **Strategy** | Job matching algorithms | Skill-based, Location-based, Experience-based |
| **Factory** | Post/Message creation | CreatePost(), CreateMessage() |
| **State** | Connection request lifecycle | Pending → Accepted/Rejected |

## 🎯 Demo Scenarios (5 Scenarios)
1. **User Profile Management** - Create profile, add skills, add experience
2. **Connection System** - Send request, accept/reject, view connections
3. **Job Posting & Application** - Post job, apply, match candidates
4. **Feed & Interactions** - Create post, like, comment, share
5. **Messaging System** - Send message, create conversation, notifications

## 🔑 Key Algorithms

### 1. Connection Recommendation Algorithm
```python
# Mutual connections scoring
score = len(mutual_connections) * 10
score += len(common_skills) * 5
score += (1 if same_company else 0) * 15
# Returns top N recommendations sorted by score
```

### 2. Job Matching Algorithm (Strategy Pattern)
```python
# Skill-based matching
match_score = (matched_skills / required_skills) * 100
# Location-based matching
match_score = distance < 50km ? 100 : 50
# Experience-based matching
match_score = abs(years_exp - required_exp) < 2 ? 100 : 70
```

### 3. Feed Ranking Algorithm
```python
# Engagement score
score = likes * 1 + comments * 3 + shares * 5
# Recency decay
score *= exp(-time_since_post / decay_factor)
# Connection strength
score *= connection_strength (0.1 to 1.0)
```

## 💡 Key Talking Points

### Pattern Explanations
**Singleton Pattern**: "We use Singleton for LinkedInSystem to ensure all users interact with the same system instance. This prevents data inconsistency and provides centralized state management."

**Observer Pattern**: "When a user creates a post, all their connections are automatically notified through the Observer pattern. The Post is the Subject, and Followers are Observers. This decouples post creation from notification logic."

**Strategy Pattern**: "Job matching uses Strategy pattern with 3 algorithms: SkillBasedMatcher, LocationBasedMatcher, and ExperienceBasedMatcher. Companies can choose which strategy to use, and we can add new matchers without modifying existing code."

**Factory Pattern**: "PostFactory creates different post types (TextPost, ImagePost, VideoPost, ArticlePost) based on content. This encapsulates creation logic and makes it easy to add new post types."

**State Pattern**: "Connection requests follow State pattern: Pending → Accepted/Rejected. Each state has specific behaviors (send notification, update connection count, etc.)."

### SOLID Principles in Action
**Single Responsibility**: User class handles profile data, ConnectionManager handles connections separately

**Open/Closed**: Strategy pattern allows new job matchers without modifying existing code

**Liskov Substitution**: All post types (TextPost, ImagePost) can substitute base Post class

**Interface Segregation**: Separate interfaces for Likeable, Commentable, Shareable

**Dependency Inversion**: Feed depends on abstract Post interface, not concrete implementations

## ✅ Success Criteria
- [ ] All 6 core entities implemented with proper attributes
- [ ] 5 design patterns clearly demonstrated with code
- [ ] At least 3 demo scenarios run successfully
- [ ] Can explain Observer pattern for feed updates
- [ ] Can explain Strategy pattern for job matching
- [ ] Connection state machine working (Pending → Accepted/Rejected)
- [ ] Feed ranking algorithm implemented
- [ ] Code follows SOLID principles

## 🚀 Quick Commands
```bash
# Run the complete working implementation
python3 INTERVIEW_COMPACT.py

# Run specific demo
python3 -c "from INTERVIEW_COMPACT import demo1_profile_management; demo1_profile_management()"

# Read detailed implementation guide
cat 75_MINUTE_GUIDE.md

# Study complete reference with UML diagrams
cat README.md
```

## 🆘 If You Get Stuck
- **Early phase (< 20 min)**: Focus on User, Connection, Post entities first. Skip Message and Job initially.
- **Mid phase (20-50 min)**: Implement Singleton and Observer patterns. Skip Strategy initially.
- **Late phase (> 50 min)**: Show 2 working demos (Profile + Connections). Explain Feed algorithm verbally.

### Minimum Viable Implementation
1. User entity with skills
2. Connection with Pending/Accepted states
3. Basic Post with likes
4. Singleton LinkedInSystem
5. Observer for post notifications
6. One demo showing user creates post → followers notified

## 📊 Complexity Reference
| Component | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| Add Connection | O(1) | O(N) connections |
| Get Feed | O(N log N) | O(N) posts |
| Search Users | O(N) or O(log N) with index | O(N) |
| Job Matching | O(N*M) N=jobs, M=users | O(1) |
| Mutual Connections | O(N) | O(N) |

## 🎓 Interview Tips
1. **Start with User & Connection** - These are the foundation
2. **Explain Observer early** - Shows you understand event-driven design
3. **Draw state diagram** - For connection request lifecycle
4. **Mention scalability** - "We'd use Redis for feed caching in production"
5. **Code defensively** - Check null, validate inputs
6. **Name variables clearly** - `pending_connection_requests` not `pcr`

---
**Remember**: LinkedIn is about **connections** and **content**. Focus on the social graph (User-Connection network) and content distribution (Post-Feed system). Show working code for these core flows!
