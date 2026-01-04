import httpx

from zvideos import openai_client

try:
    prompt = ""
    messages = [
        {"role": "user", "content": prompt}
    ]
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3,
        timeout=httpx.Timeout(600.0),  # 10-minute timeout
    )
    chatgpt_response = response.choices[0].message.content
    print("=================== GPT RESPONSE =================")
    print(chatgpt_response)
except Exception as e:
    print(f"Error during OpenAI API call: {e}")
    raise