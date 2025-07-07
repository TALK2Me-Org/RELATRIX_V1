# Mem0 Platform Documentation

## Contextual Add (ADD v2)

🔐 Mem0 is now SOC 2 and HIPAA compliant! We're committed to the highest standards of data security and privacy, enabling secure memory for enterprises, healthcare, and beyond. Learn more

Mem0 now supports an contextual add version (v2). To use it, set version="v2" during the add call. The default version is v1, which is deprecated now. We recommend migrating to v2 for new applications.

### Key Differences Between v1 and v2

#### Version 1 (Legacy)
In v1 (default), users needed to pass either the entire conversation history or past k messages with each new message to generate properly contextualized memories. This approach required:

- Manually tracking and sending previous messages using a sliding window approach
- Increased payload sizes as conversations grew longer, requiring careful window size management

Python:
```python
# First interaction
messages1 = [
    {"role": "user", "content": "Hi, I'm Alex and I live in San Francisco."},
    {"role": "assistant", "content": "Hello Alex! Nice to meet you. San Francisco is a beautiful city."}
]
client.add(messages1, user_id="alex")

# Second interaction - must include previous messages for context
messages2 = [
    {"role": "user", "content": "Hi, I'm Alex and I live in San Francisco."},
    {"role": "assistant", "content": "Hello Alex! Nice to meet you. San Francisco is a beautiful city."},
    {"role": "user", "content": "I like to eat sushi, and yesterday I went to Sunnyvale to eat sushi with my friends."},
    {"role": "assistant", "content": "Sushi is really a tasty choice. What did you do this weekend?"}
]
client.add(messages2, user_id="alex")
```

#### Version 2 (Recommended)
In v2, Mem0 automatically manages conversation context. Users only need to send new messages, and the system will:

- Automatically retrieve relevant conversation history
- Generate properly contextualized memories
- Reduce payload sizes and simplify integration

Python:
```python
# First interaction
messages1 = [
    {"role": "user", "content": "Hi, I'm Alex and I live in San Francisco."},
    {"role": "assistant", "content": "Hello Alex! Nice to meet you. San Francisco is a beautiful city."}
]
client.add(messages1, user_id="alex", version="v2")

# Second interaction - only need to send new messages
messages2 = [
    {"role": "user", "content": "I like to eat sushi, and yesterday I went to Sunnyvale to eat sushi with my friends."},
    {"role": "assistant", "content": "Sushi is really a tasty choice. What did you do this weekend?"}
]
client.add(messages2, user_id="alex", version="v2")
```

### Benefits of Using v2
- Simplified Integration: No need to track and manage conversation history
- Reduced Payload Size: Only send new messages, not the entire conversation
- Improved Memory Quality: Automatic context retrieval ensures better memory generation

### Understanding ID Parameters in v2
When using contextual add v2, you have different options for how to organize and retrieve memories:

#### Using Only user_id
When you provide only a user_id:

- Memories are associated with this user's long-term memory store
- The system will automatically retrieve relevant context from all of the user's previous conversations
- These memories persist indefinitely across all of the user's sessions
- Ideal for maintaining persistent user information (preferences, personal details, etc.)

Python:
```python
# Adding to long-term user memory
messages = [
    {"role": "user", "content": "I'm allergic to peanuts and shellfish."},
    {"role": "assistant", "content": "I've noted your allergies to peanuts and shellfish."}
]
client.add(messages, user_id="alex", version="v2")
```

#### Using user_id with run_id
When you provide both user_id and run_id:

- Memories are associated with a specific conversation session or interaction
- The system will retrieve context primarily from this specific session
- These memories are still tied to the user but are organized by the specific session
- Ideal for maintaining context within a specific conversation flow or task
- Helps prevent context from different conversations from interfering with each other

Python:
```python
# Adding to a specific conversation session
messages = [
    {"role": "user", "content": "For this trip to Paris, I want to focus on art museums."},
    {"role": "assistant", "content": "Great! I'll help you plan your Paris trip with a focus on art museums."}
]
client.add(messages, user_id="alex", run_id="paris-trip-2024", version="v2")

# Later in the same conversation session
messages2 = [
    {"role": "user", "content": "I'd like to visit the Louvre on Monday."},
    {"role": "assistant", "content": "The Louvre is a great choice for Monday. Would you like information about opening hours?"}
]
client.add(messages2, user_id="alex", run_id="paris-trip-2024", version="v2")
```

Using run_id helps you organize memories into logical sessions or tasks, making it easier to maintain context for specific interactions while still associating everything with the user's overall profile.

## Async Client

Asynchronous client for Mem0

🔐 Mem0 is now SOC 2 and HIPAA compliant! We're committed to the highest standards of data security and privacy, enabling secure memory for enterprises, healthcare, and beyond. Learn more

The AsyncMemoryClient is an asynchronous client for interacting with the Mem0 API. It provides similar functionality to the synchronous MemoryClient but allows for non-blocking operations, which can be beneficial in applications that require high concurrency.

### Initialization
To use the async client, you first need to initialize it:

Python:
```python
import os
from mem0 import AsyncMemoryClient

os.environ["MEM0_API_KEY"] = "your-api-key"

client = AsyncMemoryClient()
```

### Methods
The AsyncMemoryClient provides the following methods:

#### Add
Add a new memory asynchronously.

Python:
```python
messages = [
    {"role": "user", "content": "Alice loves playing badminton"},
    {"role": "assistant", "content": "That's great! Alice is a fitness freak"},
]
await client.add(messages, user_id="alice")
```

#### Search
Search for memories based on a query asynchronously.

Python:
```python
await client.search("What is Alice's favorite sport?", user_id="alice")
```

#### Get All
Retrieve all memories for a user asynchronously.

Python:
```python
await client.get_all(user_id="alice")
```

#### Delete
Delete a specific memory asynchronously.

Python:
```python
await client.delete(memory_id="memory-id-here")
```

#### Delete All
Delete all memories for a user asynchronously.

Python:
```python
await client.delete_all(user_id="alice")
```

#### History
Get the history of a specific memory asynchronously.

Python:
```python
await client.history(memory_id="memory-id-here")
```

#### Users
Get all users, agents, and runs which have memories associated with them asynchronously.

Python:
```python
await client.users()
```

#### Reset
Reset the client, deleting all users and memories asynchronously.

Python:
```python
await client.reset()
```

### Conclusion
The AsyncMemoryClient provides a powerful way to interact with the Mem0 API asynchronously, allowing for more efficient and responsive applications. By using this client, you can perform memory operations without blocking your application's execution.

## Advanced Retrieval

🔐 Mem0 is now SOC 2 and HIPAA compliant! We're committed to the highest standards of data security and privacy, enabling secure memory for enterprises, healthcare, and beyond. Learn more

Mem0's Advanced Retrieval provides additional control over how memories are selected and ranked during search. While the default search uses embedding-based semantic similarity, Advanced Retrieval introduces specialized options to improve recall, ranking accuracy, or filtering based on specific use case.

You can enable any of the following modes independently or together:

- Keyword Search
- Reranking
- Filtering

Each enhancement can be toggled independently via the search() API call. These flags are off by default. These are useful when building agents that require fine-grained retrieval control

### Keyword Search
Keyword search expands the result set by including memories that contain lexically similar terms and important keywords from the query, even if they're not semantically similar.

#### When to use
- You are searching for specific entities, names, or technical terms
- When you need comprehensive coverage of a topic
- You want broader recall at the cost of slight noise

#### API Usage
```python
results = client.search(
    query="What are my food preferences?",
    keyword_search=True,
    user_id="alex"
)
```

#### Example
Without keyword_search:
- "Vegetarian. Allergic to nuts."
- "Prefers spicy food and enjoys Thai cuisine"

With keyword_search=True:
- "Vegetarian. Allergic to nuts."
- "Prefers spicy food and enjoys Thai cuisine"
- "Mentioned disliking seafood during restaurant discussion"

#### Trade-offs
- Increases recall
- May slightly reduce precision
- Adds ~10ms latency

### Reranking
Reranking reorders the retrieved results using a deep semantic relevance model that improves the position of the most relevant matches.

#### When to use
- You rely on top-1 or top-N precision
- When result order is critical for your application
- You want consistent result quality across sessions

#### API Usage
```python
results = client.search(
    query="What are my travel plans?",
    rerank=True,
    user_id="alex"
)
```

#### Example
Without rerank:
- "Traveled to France last year"
- "Planning a trip to Japan next month"
- "Interested in visiting Tokyo restaurants"

With rerank=True:
- "Planning a trip to Japan next month"
- "Interested in visiting Tokyo restaurants"
- "Traveled to France last year"

#### Trade-offs
- Significantly improves result ordering accuracy
- Ensures most relevant memories appear first
- Adds ~150–200ms latency
- Higher computational cost

### Filtering
Filtering allows you to narrow down search results by applying specific criteria from the set of retrieved memories.

#### When to use
- You require highly specific results
- You are working with huge amount of data where noise is problematic
- You require quality over quantity results

#### API Usage
```python
results = client.search(
    query="What are my dietary restrictions?",
    filter_memories=True,
    user_id="alex"
)
```

#### Example
Without filtering:
- "Vegetarian. Allergic to nuts."
- "I enjoy cooking Italian food on weekends"
- "Mentioned disliking seafood during restaurant discussion"
- "Prefers to eat dinner at 7pm"

With filter_memories=True:
- "Vegetarian. Allergic to nuts."
- "Mentioned disliking seafood during restaurant discussion"

#### Trade-offs
- Maximizes precision (highly relevant results only)
- May reduce recall (filters out some relevant memories)
- Adds ~200-300ms latency
- Best for focused, specific queries

### Combining Modes
You can combine all three retrieval modes as needed:

```python
results = client.search(
    query="What are my travel plans?",
    keyword_search=True,
    rerank=True,
    filter_memories=True,
    user_id="alex"
)
```

This configuration broadens the candidate pool with keywords, improves ordering via rerank, and finally cuts noise with filtering.
Combining all modes may add up to ~450ms latency per query.

### Performance Benchmarks
| Mode | Approximate Latency |
|------|-------------------|
| keyword_search | <10ms |
| rerank | 150–200ms |
| filter_memories | 200–300ms |

### Best Practices & Limitations
- Use keyword_search for broader recall when query context is limited
- Use rerank to prioritize the top-most relevant result
- Use filter_memories in production-facing or safety-critical agents
- Combine filtering and reranking for maximum accuracy
- Filters may eliminate all results—always handle the empty set gracefully
- Filtering uses LLM evaluation and may be rate-limited depending on your plan
- You can enable or disable these search modes by passing the respective parameters to the search method. There is no required sequence for these modes, and any combination can be used based on your needs.

## Criteria Retrieval

🔐 Mem0 is now SOC 2 and HIPAA compliant! We're committed to the highest standards of data security and privacy, enabling secure memory for enterprises, healthcare, and beyond. Learn more

Mem0's Criteria Retrieval feature allows you to retrieve memories based on your defined criteria. It goes beyond generic semantic relevance and rank memories based on what matters to your application - emotional tone, intent, behavioral signals, or other custom traits.

Instead of just searching for "how similar a memory is to this query?", you can define what relevance really means for your project. For example:

- Prioritize joyful memories when building a wellness assistant
- Downrank negative memories in a productivity-focused agent
- Highlight curiosity in a tutoring agent

You define criteria - custom attributes like "joy", "negativity", "confidence", or "urgency", and assign weights to control how they influence scoring. When you search, Mem0 uses these to re-rank memories that are semantically relevant, favoring those that better match your intent.

This gives you nuanced, intent-aware memory search that adapts to your use case.

### When to Use Criteria Retrieval
Use Criteria Retrieval if:

- You're building an agent that should react to emotions or behavioral signals
- You want to guide memory selection based on context, not just content
- You have domain-specific signals like "risk", "positivity", "confidence", etc. that shape recall

### Setting Up Criteria Retrieval
Let's walk through how to configure and use Criteria Retrieval step by step.

#### Initialize the Client
Before defining any criteria, make sure to initialize the MemoryClient with your credentials and project ID:

```python
from mem0 import MemoryClient

client = MemoryClient(
    api_key="your_mem0_api_key",
    org_id="your_organization_id",
    project_id="your_project_id"
)
```

#### Define Your Criteria
Each criterion includes:

- A name (used in scoring)
- A description (interpreted by the LLM)
- A weight (how much it influences the final score)

```python
retrieval_criteria = [
    {
        "name": "joy",
        "description": "Measure the intensity of positive emotions such as happiness, excitement, or amusement expressed in the sentence. A higher score reflects greater joy.",
        "weight": 3
    },
    {
        "name": "curiosity",
        "description": "Assess the extent to which the sentence reflects inquisitiveness, interest in exploring new information, or asking questions. A higher score reflects stronger curiosity.",
        "weight": 2
    },
    {
        "name": "emotion",
        "description": "Evaluate the presence and depth of sadness or negative emotional tone, including expressions of disappointment, frustration, or sorrow. A higher score reflects greater sadness.",
        "weight": 1
    }
]
```

#### Apply Criteria to Your Project
Once defined, register the criteria to your project:

```python
client.update_project(retrieval_criteria=retrieval_criteria)
```

Criteria apply project-wide. Once set, they affect all searches using version="v2".

### Example Walkthrough
After setting up your criteria, you can use them to filter and retrieve memories. Here's an example:

#### Add Memories
```python
messages = [
    {"role": "user", "content": "What a beautiful sunny day! I feel so refreshed and ready to take on anything!"},
    {"role": "user", "content": "I've always wondered how storms form—what triggers them in the atmosphere?"},
    {"role": "user", "content": "It's been raining for days, and it just makes everything feel heavier."},
    {"role": "user", "content": "Finally I get time to draw something today, after a long time!! I am super happy today."}
]

client.add(messages, user_id="alice")
```

#### Run Standard vs. Criteria-Based Search
```python
# With criteria
filters = {
    "AND": [
        {"user_id": "alice"}
    ]
}
results_with_criteria = client.search(
    query="Why I am feeling happy today?",
    filters=filters,
    version="v2"
)

# Without criteria
results_without_criteria = client.search(
    query="Why I am feeling happy today?",
    user_id="alice"
)
```

#### Compare Results

Search Results (with Criteria):
```json
[
    {"memory": "User feels refreshed and ready to take on anything on a beautiful sunny day", "score": 0.666, ...},
    {"memory": "User finally has time to draw something after a long time", "score": 0.616, ...},
    {"memory": "User is happy today", "score": 0.500, ...},
    {"memory": "User is curious about how storms form and what triggers them in the atmosphere.", "score": 0.400, ...},
    {"memory": "It has been raining for days, making everything feel heavier.", "score": 0.116, ...}
]
```

Search Results (without Criteria):
```json
[
    {"memory": "User is happy today", "score": 0.607, ...},
    {"memory": "User feels refreshed and ready to take on anything on a beautiful sunny day", "score": 0.512, ...},
    {"memory": "It has been raining for days, making everything feel heavier.", "score": 0.4617, ...},
    {"memory": "User is curious about how storms form and what triggers them in the atmosphere.", "score": 0.340, ...},
    {"memory": "User finally has time to draw something after a long time", "score": 0.336, ...},
]
```

#### Search Results Comparison
- Memory Ordering: With criteria, memories with high joy scores (like feeling refreshed and drawing) are ranked higher, while without criteria, the most relevant memory ("User is happy today") comes first.
- Score Distribution: With criteria, scores are more spread out (0.116 to 0.666) and reflect the criteria weights, while without criteria, scores are more clustered (0.336 to 0.607) and based purely on relevance.
- Trait Sensitivity: "Rainy day" content is penalized due to negative tone. "Storm curiosity" is recognized and scored accordingly.

### Key Differences vs. Standard Search
| Aspect | Standard Search | Criteria Retrieval |
|--------|----------------|-------------------|
| Ranking Logic | Semantic similarity only | Semantic + LLM-based criteria scoring |
| Control Over Relevance | None | Fully customizable with weighted criteria |
| Memory Reordering | Static based on similarity | Dynamically re-ranked by intent alignment |
| Emotional Sensitivity | No tone or trait awareness | Incorporates emotion, tone, or custom behaviors |
| Version Required | Defaults | search(version="v2") |

If no criteria are defined for a project, version="v2" behaves like normal search.

### Best Practices
- Choose 3–5 criteria that reflect your application's intent
- Make descriptions clear and distinct, those are interpreted by an LLM
- Use stronger weights to amplify impact of important traits
- Avoid redundant or ambiguous criteria (e.g. "positivity" + "joy")
- Always handle empty result sets in your application logic

### How It Works
1. Criteria Definition: Define custom criteria with a name, description, and weight. These describe what matters in a memory (e.g., joy, urgency, empathy).
2. Project Configuration: Register these criteria using update_project(). They apply at the project level and influence all searches using version="v2".
3. Memory Retrieval: When you perform a search with version="v2", Mem0 first retrieves relevant memories based on the query and your defined criteria.
4. Weighted Scoring: Each retrieved memory is evaluated and scored against the defined criteria and weights.

This lets you prioritize memories that align with your agent's goals and not just those that look similar to the query.

Criteria retrieval is currently supported only in search v2. Make sure to use version="v2" when performing searches with custom criteria.

### Summary
- Define what "relevant" means using criteria
- Apply them per project via update_project()
- Use version="v2" to activate criteria-aware search
- Build agents that reason not just with relevance, but contextual importance

## Custom Instructions

Enhance your product experience by adding custom instructions tailored to your needs

🔐 Mem0 is now SOC 2 and HIPAA compliant! We're committed to the highest standards of data security and privacy, enabling secure memory for enterprises, healthcare, and beyond. Learn more

### Introduction to Custom Instructions
Custom instructions allow you to define specific guidelines for your project. This feature helps ensure consistency and provides clear direction for handling project-specific requirements.

Custom instructions are particularly useful when you want to:

- Define how information should be extracted from conversations
- Specify what types of data should be captured or ignored
- Set rules for categorizing and organizing memories
- Maintain consistent handling of project-specific requirements

When custom instructions are set at the project level, they will be applied to all new memories added within that project. This ensures that your data is processed according to your defined guidelines across your entire project.

### Setting Custom Instructions
You can set custom instructions for your project using the following method:

Code:
```python
# Update custom instructions
prompt ="""
Your Task: Extract ONLY health-related information from conversations, focusing on the following areas:

1. Medical Conditions, Symptoms, and Diagnoses:
   - Illnesses, disorders, or symptoms (e.g., fever, diabetes).
   - Confirmed or suspected diagnoses.

2. Medications, Treatments, and Procedures:
   - Prescription or OTC medications (names, dosages).
   - Treatments, therapies, or medical procedures.

3. Diet, Exercise, and Sleep:
   - Dietary habits, fitness routines, and sleep patterns.

4. Doctor Visits and Appointments:
   - Past, upcoming, or regular medical visits.

5. Health Metrics:
   - Data like weight, BP, cholesterol, or sugar levels.

Guidelines:
- Focus solely on health-related content.
- Maintain clarity and context accuracy while recording.
"""
response = client.update_project(custom_instructions=prompt)
print(response)
```

You can also retrieve the current custom instructions:

Code:
```python
# Retrieve current custom instructions
response = client.get_project(fields=["custom_instructions"])
print(response)
```

## Group Chat

Enable multi-participant conversations with automatic memory attribution to individual speakers

📢 Announcing our research paper: Mem0 achieves 26% higher accuracy than OpenAI Memory, 91% lower latency, and 90% token savings! Read the paper to learn how we're revolutionizing AI agent memory.

### Introduction to the Group Chat

#### Overview
The Group Chat feature enables Mem0 to process conversations involving multiple participants and automatically attribute memories to individual speakers. This allows for precise tracking of each participant's preferences, characteristics, and contributions in collaborative discussions, team meetings, or multi-agent conversations.

When you provide messages with participant names, Mem0 automatically:

- Extracts memories from each participant's messages separately
- Attributes each memory to the correct speaker using their name as the user_id or agent_id
- Maintains individual memory profiles for each participant

#### How Group Chat Works
Mem0 automatically detects group chat scenarios when messages contain a name field:

```json
{
  "role": "user",
  "name": "Alice",
  "content": "Hey team, I think we should use React for the frontend"
}
```

When names are present, Mem0:

- Formats messages as "Alice (user): content" for processing
- Extracts memories with proper attribution to each speaker
- Stores memories with the speaker's name as the user_id (for users) or agent_id (for assistants/agents)

#### Memory Attribution Rules
- User Messages: The name field becomes the user_id in stored memories
- Assistant/Agent Messages: The name field becomes the agent_id in stored memories
- Messages without names: Fall back to standard processing using role as identifier

### Using Group Chat

#### Basic Group Chat
Add memories from a multi-participant conversation:

Python:
```python
from mem0 import MemoryClient

client = MemoryClient(api_key="your-api-key")

# Group chat with multiple users
messages = [
    {"role": "user", "name": "Alice", "content": "Hey team, I think we should use React for the frontend"},
    {"role": "user", "name": "Bob", "content": "I disagree, Vue.js would be better for our use case"},
    {"role": "user", "name": "Charlie", "content": "What about considering Angular? It has great enterprise support"},
    {"role": "assistant", "content": "All three frameworks have their merits. Let me summarize the pros and cons of each."}
]

response = client.add(
    messages,
    run_id="group_chat_1",
    output_format="v1.1",
    infer=True
)
print(response)
```

### Retrieving Group Chat Memories

#### Get All Memories for a Session
Retrieve all memories from a specific group chat session:

Python:
```python
# Get all memories for a specific run_id
filters = {
    "AND": [
        {"user_id": "*"},
        {"run_id": "group_chat_1"}
    ]
}

all_memories = client.get_all(version="v2", filters=filters, page=1)
print(all_memories)
```

#### Get Memories for a Specific Participant
Retrieve memories from a specific participant in a group chat:

Python:
```python
# Get memories for a specific participant
filters = {
    "AND": [
        {"user_id": "charlie"},
        {"run_id": "group_chat_1"}
    ]
}

charlie_memories = client.get_all(version="v2", filters=filters, page=1)
print(charlie_memories)
```

#### Search Within Group Chat Context
Search for specific information within a group chat session:

Python:
```python
# Search within group chat context
filters = {
    "AND": [
        {"user_id": "charlie"},
        {"run_id": "group_chat_1"}
    ]
}

search_response = client.search(
    query="What are the tasks?",
    filters=filters,
    version="v2"
)
print(search_response)
```

### Async Mode Support
Group chat also supports async processing for improved performance:

Python:
```python
# Group chat with async mode
response = client.add(
    messages,
    run_id="groupchat_async",
    output_format="v1.1",
    infer=True,
    async_mode=True
)
print(response)
```

### Message Format Requirements

#### Required Fields
Each message in a group chat must include:

- role: The participant's role ("user", "assistant", "agent")
- content: The message content
- name: The participant's name (required for group chat detection)

#### Example Message Structure
```json
{
  "role": "user",
  "name": "Alice",
  "content": "I think we should use React for the frontend"
}
```

#### Supported Roles
- user: Human participants (memories stored with user_id)
- assistant: AI assistants (memories stored with agent_id)

### Best Practices
1. Consistent Naming: Use consistent names for participants across sessions to maintain proper memory attribution.

2. Clear Role Assignment: Ensure each participant has the correct role (user, assistant, or agent) for proper memory categorization.

3. Session Management: Use meaningful run_id values to organize group chat sessions and enable easy retrieval.

4. Memory Filtering: Use filters to retrieve memories from specific participants or sessions when needed.

5. Async Processing: Use async_mode=True for large group conversations to improve performance.

6. Search Context: Leverage the search functionality to find specific information within group chat contexts.

### Use Cases
- Team Meetings: Track individual team member preferences and contributions
- Customer Support: Maintain separate memory profiles for different customers
- Multi-Agent Systems: Manage conversations with multiple AI assistants
- Collaborative Projects: Track individual preferences and expertise areas
- Group Discussions: Maintain context for each participant's viewpoints

If you have any questions, please feel free to reach out to us using one of the following methods: