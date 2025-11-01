curl -sS https://router.huggingface.co/v1/chat/completions \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-20b:groq",
    "messages": [{"role":"user","content":"日本語で1文自己紹介"}]
  }' | jq -r '.choices[0].message.content'
