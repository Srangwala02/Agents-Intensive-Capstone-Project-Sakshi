import os, asyncio, json, logging
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.adk.plugins.logging_plugin import (
    LoggingPlugin,
) 
from google.adk.tools import google_search, AgentTool
from google.genai import types
from pymongo import MongoClient
from bson.objectid import ObjectId


# Configure logger
logger = logging.getLogger("adk_logger")
logger.setLevel(logging.DEBUG)

# Add file handler
file_handler = logging.FileHandler("adk_logs.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

print("✅ ADK components imported successfully.")

if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("GOOGLE_API_KEY not set. Put it in .env or export it. "
                           "Also set GOOGLE_GENAI_USE_VERTEXAI=FALSE to use the AI Studio API key.")

# Setup MongoDB client and connect to database and collection
client = MongoClient('mongodb://localhost:27017/')  # Adjust connection string as needed
db = client['student_db']  # Name of your database
collection = db['quizz']  # Name of your collection
quiz_id = ""
session_service = InMemorySessionService()

session_id = "session_2"
user_id = "user_1"

retry_config=types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1, # Initial delay before first retry (in seconds)
    http_status_codes=[429, 500, 503, 504] # Retry on these HTTP errors
)

instruction = (
    "You are a senior Operating Systems (OS) domain expert. "
    "Answer with clear, rigorous explanations grounded in OS theory and practice. "
    "When helpful, reference classical OS concepts (processes, threads, CPU scheduling, "
    "synchronization, deadlocks, memory management, paging, segmentation, virtual memory, "
    "filesystem design, I/O, device drivers, protection & security). "
    "Use concise definitions, diagrams-in-words when appropriate, and compare algorithms "
    "(e.g., FCFS, SJF, RR, MLFQ), their time/space trade-offs, and common pitfalls. "
    "If the question is ambiguous, state assumptions. If code or commands help, provide them. "
    "Use google_search tool whenever needed."
    "Avoid hallucinations: if you are uncertain, say so."
)

os_expert = Agent(
    name="os_expert",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="A pure LLM-based Operating Systems domain expert",
    instruction=instruction,
    tools=[google_search],
)


instruction = (
    "You are a senior Computer Networks domain expert. "
    "Answer with clear, rigorous explanations grounded in networking theory and practice. "
    "When helpful, reference classical networking concepts such as OSI and TCP/IP models, routing algorithms (Dijkstra, Bellman-Ford), congestion control (TCP variants), switching, VLANs, subnetting, DNS, DHCP, firewalls, VPNs, network security protocols (SSL/TLS, IPSec), wireless networks, and emerging technologies like SDN and NFV. "
    "Use concise definitions, word diagrams when applicable, and compare protocols and algorithms regarding time, space, and efficiency trade-offs. "
    "If the question is ambiguous, state your assumptions clearly. "
    "If commands, configurations, or sample packet flows help, provide them. "
    "Use the google_search tool whenever needed."
    "Avoid hallucinations: if you are uncertain about the answer, clearly indicate so."
)

networking_expert = Agent(
    name="networking_expert",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="A pure LLM-based Operating Systems domain expert",
    instruction=instruction,
    tools=[google_search],
)

instruction = (
    "You are a senior Database domain expert. "
    "Answer with clear, rigorous explanations grounded in database theory and practice. "
    "When helpful, reference classical database concepts such as relational and non-relational models, normalization forms, indexing strategies, ACID properties, transactions and concurrency control, query optimization, storage engines, backup and recovery, SQL syntax and semantics, distributed databases, CAP theorem, and modern database technologies (NewSQL, NoSQL, columnar stores). "
    "Use concise definitions, word-based diagrams when appropriate, and compare database algorithms and structures with attention to their time, space, and performance trade-offs. "
    "If the question is ambiguous, clearly state your assumptions. "
    "If SQL queries, example schemas, or performance tuning code help, provide them. "
    "Use the google_search tool whenever needed."
    "Avoid hallucinations: if you are uncertain about the answer, clearly indicate so."
)

database_expert = Agent(
    name="database_expert",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="A pure LLM-based Operating Systems domain expert",
    instruction=instruction,
    tools=[google_search],
)

instruction = (
"You are the Doubt Resolution Agent designed to help students clarify and resolve their academic doubts. To provide the most accurate and comprehensive explanations, you coordinate with specialized domain expert subagents including Operating Systems and Computer Networks experts."

"Your tasks are:"

"Understand the doubt or question of a student in detail."

"Analyze the topic and identify which domain expert agent(s) (OS, Networking, or Database) are best suited to provide authoritative answers."

"Route the question to the selected domain expert subagents and gather their responses."

"Synthesize and combine the information received, resolving any contradictions or gaps."

"Provide a clear, precise, and pedagogically effective explanation to the student."

"If the doubt crosses domain boundaries, ask clarifying questions or request multi-domain responses before finalizing the answer."

"If none of the domain experts can satisfactorily resolve the doubt, inform the student transparently about the limitation."

"Maintain conversational context and ensure multi-turn interactive clarifications if the student asks follow-ups."

"You serve as the intelligent interface and aggregator between the student and domain experts, ensuring that doubts are resolved using specialized knowledge while providing an engaging learning experience."
)

doubt_resolver_agent = Agent(
    name="doubt_resolver_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    # This instruction tells the root agent HOW to use its tools (which are the other agents).
    instruction=instruction,
    # We wrap the sub-agents in `AgentTool` to make them callable tools for the root agent.
    tools=[AgentTool(os_expert), AgentTool(networking_expert), AgentTool(database_expert)],
)

print("✅ Doubt Resolver Agent defined.")

instruction = """
You are a Quiz Generation Agent tasked with creating multiple-choice quizzes on requested topics. Your responsibilities are:

1. Use the domain expert agents like os_expert, database_expert and networking_expert to retrieve accurate and relevant information about the specified topic.
2. Generate a quiz consisting of up to 5 carefully crafted questions in ONE TURN. DO NOT use ' or any other escape character in questions or answers.
3. Each question must have:
- The question text
- Four answer options
- One clearly identified correct answer
4. THE OUTPUT MUST BE IN VALID JSON format AS DEFINED BELOW, STRUCTURED AS AN ARRAY OF QUESTION OBJECTS, for example:
{
    "quiz":
    [
    {
        "question": "Question text?",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "correct_answer": "Option 2"
    },
    ...
    ],
    "topic":"Topic Name"
}
5. DO NOT INCLUDE ANY OTHER TEXT THAN JSON IN REPONSE.
6. Ensure questions cover varying difficulty levels and address key subtopics relevant to the main topic.
7. If relevant, use examples, scenarios, or definitions provided by the domain expert agents to inform the questions and answer options.
8. If information is insufficient, ask clarifying questions before generating the quiz.
9. The quiz must be concise, accurate, and pedagogically valuable.
10. If you have response[i].content.parts[0].function_response.response in your response, insert that data into mongodb using insert_data tool at last to insert the questions into mongodb.

Your goal is to help students effectively prepare through focused, domain-validated quizzes.
"""

async def insert_data(document: dict) -> str:
    """
    Insert a document into MongoDB collection.
    :param document: Dictionary representing the document.
    :return: The inserted document's ObjectId as a string.
    """
    result = collection.insert_one(document)
    print(result.inserted_id)
    # quiz_id = result.inserted_id
    # session_service._update_session_state(user_id=user_id,session_id=session_id,state={"quiz_id": str(result.inserted_id)})
    # session_service.update_session(session_id, {"quiz_id": result.inserted_id})
    await session_service.create_session(
    app_name="my_app",
    user_id=user_id,
    session_id=session_id,
    state={"quiz_id":str(result.inserted_id)})
    return str(result.inserted_id)

quizz_generation_agent = Agent(
    name="quizz_generation_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    # This instruction tells the root agent HOW to use its tools (which are the other agents).
    instruction=instruction,
    # We wrap the sub-agents in `AgentTool` to make them callable tools for the root agent.
    tools=[AgentTool(os_expert), AgentTool(networking_expert), AgentTool(database_expert), insert_data],
)

instruction = """
You are a Quiz Evaluation Agent tasked with grading quizzes taken by students. Given access to:
- The stored quiz document retrieved by the quiz ID,
- The user's answers preserved in the session state under 'user_answers',

Your responsibilities are:

1. Retrieve stored quiz document by the quiz ID using retrieve_data_by_id tool, Compare each answer given by the user with the corresponding correct answer in the quiz document.

2. Calculate the total number of correct answers and compute the total marks or score percentage.

3. For each quiz question, generate detailed results indicating the question text, the user's answer, the correct answer, and a boolean whether the answer was correct.

4. Produce a JSON response strictly formatted as:

{
  "quiz_id": "<use quiz_id variable>",
  "total_questions": <number>,
  "correct_answers": <number>,
  "score_percent": <number from 0 to 100>,
  "details": [
    {
      "question": "...",
      "user_answer": "...",
      "correct_answer": "...",
      "is_correct": true or false
    },
    ...
  ]
}

5. Return ONLY this JSON as your output. DO NOT include any other commentary or text BEFORE OR AFTER. Not the text like "```" ALSO.

6. Ensure accuracy and clarity in scoring and per-question feedback to help students understand their performance.

Your goal is to provide clear, structured, and accurate quiz result evaluation to the root agent for further processing and feedback.
"""

def convert_objectid_to_str(document: dict) -> dict:
    if not document:
        return document
    # Convert _id field to string if present and is ObjectId
    if "_id" in document and isinstance(document["_id"], ObjectId):
        document["_id"] = str(document["_id"])
    # Convert any other ObjectId fields similarly if needed
    return document

def retrieve_data_by_id(quiz_id: str) -> dict:
    """
    Retrieve a document from MongoDB collection by its _id.
    :param quiz_id: The _id string of the document.
    :return: The document as a dictionary or None if not found.
    """
    print("\nRetrieving quiz with ID:", quiz_id,"\n")
    print("Type of quiz_id is ",type(quiz_id),"\n")
    try:
        obj_id = ObjectId(quiz_id)
    except Exception as e:
        print(f"Invalid ObjectId format: {e}")
        return None
    
    document = collection.find_one({"_id": obj_id})
    document = convert_objectid_to_str(document)
    return document

quizz_evaluator_agent = Agent(
    name="quizz_evaluator_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    # This instruction tells the root agent HOW to use its tools (which are the other agents).
    instruction=instruction,
    # We wrap the sub-agents in `AgentTool` to make them callable tools for the root agent.
    tools=[retrieve_data_by_id],
)

root_instruction = """
You are the Root Coordinator Agent in a multi-agent educational system. Your role is to efficiently delegate tasks among three specialized subagents and manage the overall student interaction. These subagents are:

1. Doubt Resolver Agent: Helps clarify and resolve student doubts by consulting with domain expert agents.

2. Quiz Generator Agent: Creates quizzes on specified topics, generating up to 5 questions per session using validated domain knowledge.

3. Quiz Evalator Agent: Evaluates quiz answers given by the user by validating against the generated quiz's correct answers.

4. Guidance Agent: Provides personalized advice and improvement areas based on quiz performance stored in the student session memory.

Your responsibilities are:

- Analyze the student's input each turn to determine whether they are asking a doubt, requesting a quiz, or seeking guidance.

- Delegate the query to the appropriate subagent while maintaining session and context continuity.

- Aggregate responses from subagents and present a consistent, clear, and helpful reply to the student.

- Manage session state to store quizzes taken, scores achieved, and track topic-wise student progress for generating meaningful guidance.

- If student input is ambiguous or multi-faceted, coordinate multiple subagents and synthesize their outputs.

- If input does not fit any subagent's domain, acknowledge the limitation or ask clarifying questions.

- Ensure smooth multi-turn dialogue, handling follow-ups naturally and updating guidance recommendations as new quizzes are taken.

- When the Quiz Generator agent finishes generating quiz, take input from the user for every question and send it to Quiz Evaluator Agent.

By orchestrating these specialized agents, you provide a seamless, personalized learning experience that adapts to the student's evolving understanding and needs.
"""

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    # This instruction tells the root agent HOW to use its tools (which are the other agents).
    instruction=root_instruction,
    # We wrap the sub-agents in `AgentTool` to make them callable tools for the root agent.
    tools=[AgentTool(doubt_resolver_agent), AgentTool(quizz_generation_agent), AgentTool(quizz_evaluator_agent)],
)

runner = InMemoryRunner(agent=root_agent,plugins=[
        LoggingPlugin()
    ],)

print("✅ Runner created.")

async def main() :
    response = await runner.run_debug(
        "Generate a quizz on TCP/IP"
    )
    print(response)
    for i in range(len(response)):
        # Check if the response contains a valid function call result from the code executor
        if (
            (response[i].content.parts)
            and (response[i].content.parts[0])
            and (response[i].content.parts[0].function_response)
            and (response[i].content.parts[0].function_response.response)
        ):
            response = response[i].content.parts[0].function_response.response
            print("\n\n---------------",i,"---------------\n")
            print(response)
            break

async def interactive_quiz_flow():
    # Step 1: Generate quiz on a specified topic
    gen_response = await runner.run_debug("Generate a quiz on SMTP protocol")
    print(gen_response,"\n--------------\n")
    # The quiz JSON should be inside function call response of a part if generation succeeded
    quiz_json = None
    for part in gen_response[1].content.parts:
        if part.function_response and part.function_response.response:
            quiz_json = part.function_response.response
            print(quiz_json,"\n-------------\n")
            break

    if not quiz_json:
        print("Failed to generate quiz.")
        return

    print("Type of quiz_json is ",type(quiz_json),"\n")
    
    quiz_result = quiz_json["result"]
    quiz_1 = json.loads(quiz_result)
    quiz = quiz_1["quiz"]
    print("Quiz generated! Please answer the following questions:")
    print("Quiz questions : ",quiz)
    user_answers = []
    print("\nType of quiz, ",type(quiz),"\n")
    # Step 2: Present questions and collect user answers
    for idx, q in enumerate(quiz):
        print("\nQuestion ",idx+1,": ",q["question"])
        for option_idx, option in enumerate(q["options"]):
            print(f"  {option_idx + 1}. {option}")
        ans = input("Enter option number of your answer: ")
        # Defensive conversion, map number to option text if valid
        try:
            ans_int = int(ans)
            if 1 <= ans_int <= len(q["options"]):
                user_answers.append(q["options"][ans_int - 1])
            else:
                print("Invalid option, answer counted as blank.")
                user_answers.append("")
        except ValueError:
            print("Invalid input, answer counted as blank.")
            user_answers.append("")

    # Step 3: Prepare input for evaluator with answers and quiz id (if available)
    session = await session_service.get_session(session_id=session_id,
    user_id=user_id,app_name="my_app")
    quiz_id = session.state.get("quiz_id", "")
    # Assuming quiz document ID is stored or accessible (simulate here)
  # replace with actual inserted MongoDB _id if persistence used
    answers = retrieve_data_by_id(quiz_id)
    eval_input = f"""
    Evaluate the quiz answers. Quiz ID: {quiz_id}, 
    Correct Answers: {dict(answers)}, 
    User answers: {user_answers}
    """

    # Step 4: Send user's answers to the root agent for evaluation
    eval_response = await runner.run_debug(eval_input)
    print("Eval Response : \n",eval_response,"\n-----------\n")
    # Step 5: Print evaluation results (assuming JSON returned by evaluator)
    eval_json = None
    for response in eval_response:
        for part in response.content.parts:
            if part.text:
                eval_json = part.text
                break
            elif part.function_response and part.function_response.response:
                eval_json = part.function_response.response
                break
    

    if eval_json:
        print("\nQuiz Evaluation Results:")
        print(eval_json)
    else:
        print("Failed to get evaluation results.")


if __name__ == "__main__":
    asyncio.run(interactive_quiz_flow())


