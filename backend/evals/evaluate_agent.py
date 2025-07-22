import asyncio
from openai import AsyncOpenAI
from backend.evals.agent_runner_non_streaming import run_agent
from evaluation_data import EVALUATION_SAMPLES

openai = AsyncOpenAI()  # Make sure to set OPENAI_API_KEY in your environment

async def judge_answer(question: str, expected: str, actual: str) -> bool:
    """Uses GPT to judge if actual answer matches the expected one."""
    prompt = f"""
        You are an evaluator judging a data analysis assistant.

        Question:
        {question}

        Expected Answer:
        {expected}

        Actual Answer:
        {actual}

        Instructions:
        - Ignore time components like '23:00:00' unless the question explicitly asks for time.
        - Accept variations in date format (e.g., 2025-08-09 == 09-Aug-2025 == August 9th, 2025).
        - Accept answers if they are equivalent in meaning or numerically correct, even if phrased differently.
        - DO NOT reject based on formatting differences alone.
        - Focus on the **core correctness** of values (e.g., date, number, logic).

        Respond with:
        - YES: if the actual answer is factually correct or equivalent to the expected answer.
        - NO: if the actual answer is incorrect or doesn't fulfill the question.
    """

    response = await openai.chat.completions.create(
        model="gpt-4o-mini",  # Use GPT-4o for best accuracy
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    reply = response.choices[0].message.content.strip().lower()
    return "yes" in reply

async def evaluate():
    total = len(EVALUATION_SAMPLES)
    passed = 0

    for idx, sample in enumerate(EVALUATION_SAMPLES, start=1):
        print(f"\n🔍 [{idx}/{total}] Q: {sample['question']}")

        try:
            agent_answer = await run_agent(sample["question"])  # Run your agent
            print(f"🧠 Agent Answer: {agent_answer}")
            print(f"✅ Expected: {sample['expected_answer']}")

            correct = await judge_answer(sample["question"], sample["expected_answer"], agent_answer)
            if correct:
                print("✅ Match: PASSED")
                passed += 1
            else:
                print("❌ Match: FAILED")
        except Exception as e:
            print(f"⚠️ Error during evaluation: {str(e)}")

    print(f"\n📊 Final Score: {passed}/{total} correct ({(passed/total)*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(evaluate())
