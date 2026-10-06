import logging, time
logging.basicConfig(level=logging.INFO)
import image_composer

tests = [
    {
        "text": "Your brain generates enough electricity to power a small light bulb 24/7.",
        "tag": "SCIENCE",
        "prompt": "3D glowing human brain floating in deep space, electric sparks and neural lightning bolts radiating outward, dark teal background, cinematic, ultra-realistic digital art, no text"
    },
    {
        "text": "Ancient Egyptians slept on stone pillows — they believed soft pillows attracted evil spirits.",
        "tag": "HISTORY",
        "prompt": "Ancient Egyptian pharaoh stone carved pillow artifact glowing gold on dark teal museum background, 3D ultra-realistic, cinematic lighting, no text"
    },
    {
        "text": "Spending just 20 minutes in nature lowers your cortisol levels and reduces stress by 28%.",
        "tag": "HEALTH",
        "prompt": "3D glowing green leaf and relaxed human silhouette surrounded by floating nature particles and soft forest light, dark teal space-like background, cinematic, ultra-realistic, no text"
    },
]

for i, t in enumerate(tests, 1):
    path = f"test_image_{i}.jpg"
    print(f"\n--- Generating test image {i}: {t['tag']} ---")
    image_composer.compose_image(
        image_prompt=t["prompt"],
        rewritten_text=t["text"],
        topic_tag=t["tag"],
        output_path=path
    )
    if i < len(tests):
        time.sleep(5)
print("\nDone!")
