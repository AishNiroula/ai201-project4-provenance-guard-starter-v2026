import requests

URL = "http://127.0.0.1:5000/submit"
tests = {
 "clearly AI": "Artificial intelligence is transforming the way we live and work. It offers numerous benefits across many industries. Organizations can improve efficiency and reduce costs. Moreover, it enables better decision making through data analysis. In conclusion, artificial intelligence is an important technology for the future.",
 "clearly human": "Honestly? I almost quit. The bus was late, my phone died, and I stood in the rain for forty minutes. Then, out of nowhere, a stranger shared her umbrella. We talked about nothing—dogs, mostly. I got home soaked and weirdly happy.",
 "plain human": "I went to the store after work. I bought milk and eggs. The line was long so I waited. Then I drove home and made dinner. It was a pretty normal day.",
 "edited AI": "Artifical intelligence is changing how we live and work, and it's got benefits in lots of industries. Organizations can improve efficiency and cut costs. Moreover, it enables better decision making through data analysis. In conclusion, AI is an important technology for the future.",
}
print(f"{'input':15} {'model':>6} {'style':>6} {'comb':>6}  guess")
for name, text in tests.items():
    r = requests.post(URL, json={"text": text, "creator_id": "test"}).json()
    print(f"{name:15} {r['model_score']:>6} {r['style_score']:>6} {r['combined_score']:>6}  {r['guess']}")
