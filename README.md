# 🏨 Hotel Data Analysis Agent

An LLM-powered system to analyze structured hotel Excel files and return accurate insights.

This project includes:

- 🚀 FastAPI backend with streaming and guardrails  
- 💬 Streamlit frontend for chat interaction  
- 🛡️ Input guardrail agent to reject irrelevant queries  
- 📊 Evaluation engine using GPT as judge  
- 📁 Result logging with timestamps  

---

## 🗂️ Project Structure

```bash
.
├── backend/
│   ├── helpers/
│   │   ├── agent_instructions.py           # System prompt/instructions
│   │   ├── code_executor.py                # Safe Python exec function
│   │   └── excel_file_reader.py            # Reads Excel sheets with custom headers
│   ├── app.py                              # Main FastAPI backend and agent logic
│   ├── input_guardrail_agent.py            # Guardrail agent for domain restriction
│   ├── evals/
│   │   ├── evaluate_agent.py               # Evaluates agent using LLM-as-a-judge
│   │   ├── agent_runner_non_streaming.py   # Runs agent in non-stream mode
│   │   ├── evaluation_data.py              # Ground-truth QA samples
│   │   └── result_logs/                    # Stores evaluation logs
│   │       └── eval_results_<timestamp>.txt
│   └── ...
├── frontend/
│   └── hotel_data_chat_ui.py               # Streamlit UI (optional)
├── data/
│   ├── OCOnboardingInformation.xlsx        # Sample onboarding data
│   └── TheAlexIdeas27_June_2025.xlsx       # Main hotel dataset
├── trials/
│   └── (Independent test scripts used during development)
├── .env                                    # Contains OPENAI_API_KEY, TOKEN, etc.
├── requirements.txt                        # Project dependencies
└── README.md                               # ← You're here
```

---

## 🚀 Features

### 🧠 1. Agent Capabilities

* Reads structured Excel files
* Uses tools like `read_sheet_with_custom_header` and `execute_function_safely_using_exec`
* Parses user queries to extract required sheets, columns, and metrics
* Provides calculations and summaries using real data

### 🛡️ 2. Input Guardrail

Rejects non-hotel-related questions using a mini LLM-based agent.
Example rejections:

* ❌ “What is the GDP of India?”
* ❌ “Tell me a joke”

Allowed examples:

* ✅ “What is the room revenue in January?”
* ✅ “Compare occupancy between August and September”

### 💬 3. FastAPI Backend

* `/api/v1/chat` — POST endpoint to stream agent response
* Guardrails integrated before processing
* SSE streaming enabled with `StreamingResponse`

### 📊 4. Evaluation Engine (LLM-as-a-Judge)

* Located in `backend/evals/evaluate_agent.py`
* Uses GPT to check if agent output matches expected answers
* Stores results in `backend/evals/result_logs/` with timestamped logs

---

## 🧪 Running Evaluation

```bash
PYTHONPATH=. python backend/evals/evaluate_agent.py
```

* Results saved in: `backend/evals/result_logs/eval_results_<day-month-year-hh-mm>.txt`

---

## 🖥️ Run Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create `.env` file

```
OPENAI_API_KEY=your_openai_key
TOKEN=your_custom_auth_token
```

### 3. Start FastAPI backend

```bash
uvicorn backend.app:app --reload
```

### 4. (Optional) Start Streamlit frontend

```bash
streamlit run frontend/hotel_data_chat_ui.py
```

---

## 📦 API Example

```http
POST /api/v1/chat
Authorization: Bearer <TOKEN>

{
  "messages": [
    { "role": "user", "content": "What is the total room revenue in January?" }
  ]
}
```

---

## 📁 Eval Logs

* Automatically saved under `backend/evals/result_logs/` with human-readable timestamps.
* Includes detailed comparison for each evaluation sample.

---

## 📎 Future Improvements

* Add RAG-based schema understanding
* More comprehensive evaluation metrics (precision, recall)
* UI-based metrics dashboard

---

## 👨‍💻 Maintained by

* **Chandraprakash Pal**
* **https://github.com/cp-coder1269**
* **cppal474@gmail.com**

---

## 📝 License

MIT License
