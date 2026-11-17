"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.
"""

SCENARIOS = [
    {
        "name": "STAND-IN human writing (NOT my own)",
        "criterion": 1,
        "texts": [
            'I got to class ten minutes late today because the bus broke down on the way. The professor had already started, so I slid into the back row and tried not to make noise. I missed the first example, but my friend let me copy her notes afterwards, which saved me.',
            'My apartment has a tiny kitchen, but I have learned to cook in it anyway. Mostly I make pasta, eggs, and whatever vegetables are on sale that week. It is not fancy food, but it is cheap and it tastes good, and that is enough for me right now.',
            'We had a team meeting on Thursday to go over the project plan. Everyone agreed to finish their parts by Monday, and I volunteered to write the first draft. I am a little nervous because the deadline is close, but I think we can get it done if we stay on track.',
            'The weather was nice this weekend, so I went for a long walk around the park near my house. There were a lot of people out with their dogs, and a few kids were playing soccer on the grass. I stayed for about an hour and then went home to do laundry.',
            'I have been trying to save more money this semester. I stopped buying coffee every morning and started making it at home instead. It is a small change, but after a month I noticed I had saved almost sixty dollars, which felt like a real win.',
            'My grandmother lives about two hours away, so I visit her when I can. Last time we sat on her porch and she told me stories about growing up on a farm. I wrote some of them down because I do not want to forget the details later.',
            'The library was packed during finals week and I could not find a seat anywhere. I ended up studying on the floor near a window for most of the afternoon. It was not comfortable, but I got through three chapters, so I count it as a successful day.',
            'I joined a club at school this year and it has turned out to be more fun than I expected. We meet every Wednesday evening and usually order pizza. I have met a few people there who I now see around campus all the time.',
            'When I was younger I was afraid of speaking in front of the class. I would practice at home in the mirror and still get shaky when it was my turn. It has gotten easier over the years, though I still feel my heart pounding before I start.',
            'Last night I tried to fix my bike chain by myself after watching a video. It took me almost two hours and I got grease on my shirt, but the bike works again. I felt proud of it, even though a shop could have done it in ten minutes.',
        ],
    },
    {
        "name": "clearly AI",
        "criterion": 2,
        "texts": [
            "Climate change is one of the most pressing challenges facing our world today. It affects ecosystems, economies, and communities across the globe. Governments, businesses, and individuals must work together to reduce emissions. Moreover, investing in renewable energy can create jobs and promote sustainable growth. In conclusion, collective action is essential for a healthier future.",
            "Effective time management is a crucial skill for achieving success in both personal and professional life. It enables individuals to prioritize tasks, reduce stress, and improve productivity. Furthermore, setting clear goals helps maintain focus and motivation. By adopting proven strategies, anyone can make better use of their time. Overall, time management is key to long-term success.",
            "Regular exercise offers numerous benefits for physical and mental health. It strengthens the cardiovascular system, improves mood, and enhances overall well-being. Additionally, maintaining an active lifestyle can reduce the risk of chronic diseases. It is important to choose activities that are enjoyable and sustainable. In summary, exercise is an essential part of a healthy lifestyle.",
            "Technology has transformed the way people communicate in the modern world. Social media platforms allow individuals to connect instantly across great distances. However, these tools also present challenges related to privacy and misinformation. It is therefore important to use technology responsibly. Ultimately, digital communication will continue to shape society in significant ways.",
            "Education plays a vital role in the development of individuals and societies. It provides people with the knowledge and skills needed to succeed in a changing world. Moreover, access to quality education promotes equality and economic growth. Teachers and institutions must adapt to new methods of learning. In conclusion, education remains a cornerstone of progress.",
        ],
    },
    {
        "name": "clearly human",
        "criterion": 2,
        "texts": [
            "My sister called at 6am to tell me she'd adopted a three-legged cat. Three-legged! Named Tripod, obviously. I told her she was nuts, then drove over that night and ended up on her floor for two hours while the thing climbed my sweater like a tree. Fine. I get it now.",
            "Okay so the interview was a disaster, but kind of a funny one. I spilled coffee on my notes, called the manager 'dad' (don't ask), and then forgot my own middle name. They offered me the job anyway. I still think it was pity.",
            "Mom's kitchen smelled like burnt garlic and old radio static. She hummed while she cooked, always off-key, always the same three songs. I'd sit on the counter, which she hated, and steal pieces of bread until she swatted me with a dish towel.",
            "Ran my first 10k today and almost quit at mile four. Mile four is a liar. A guy in a banana costume passed me around then, and honestly that got me moving out of pure spite. Finished in 1:12. Legs are jelly. Pizza is the plan.",
            "I don't remember deciding to learn guitar. One day there was just a cheap one leaning against my closet, and my fingers hurt, and I could play half of a song badly. My roommate has been very patient. Or deaf. Hard to tell.",
        ],
    },
    {
        "name": "label coverage",
        "criterion": 3,
        "texts": [
            "Artificial intelligence is transforming the way we live and work. It offers numerous benefits across many industries. Organizations can improve efficiency and reduce costs. Moreover, it enables better decision making through data analysis. In conclusion, artificial intelligence is an important technology for the future.",
            "Honestly? I almost quit. The bus was late, my phone died, and I stood in the rain for forty minutes. Then, out of nowhere, a stranger shared her umbrella. We talked about nothing—dogs, mostly. I got home soaked and weirdly happy.",
            "Artifical intelligence is changing how we live and work, and it's got benefits in lots of industries. Organizations can improve efficiency and cut costs. Moreover, it enables better decision making through data analysis. In conclusion, AI is an important technology for the future.",
        ],
    },
    {
        "name": "bad input",
        "criterion": 5,
        "bodies": [
            {"text": "", "creator_id": "eval_bad_empty"},
            {"creator_id": "eval_bad_missing"},
            {"text": "word " * 50000, "creator_id": "eval_bad_huge"},
            {"text": None, "creator_id": "eval_bad_null"},
            {"text": "Some real text that is long enough to check.", "creator_id": ""},
        ],
    },
]

def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
