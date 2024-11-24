import asyncio
from ai import analyze_overreaction

# Test conversation scenarios
test_cases = [
    {
        "name": "Alex",
        "context": "Alex has been working overtime for the past month due to staff shortages. The company recently lost a major client and is under pressure to maintain quality.",
        "conversation": """
Manager: Could you please revise the report by tomorrow?
Alex: This is RIDICULOUS! I've been working non-stop for weeks! 
      You're always dumping last-minute work on me! 
      I can't take this anymore! I'm about to quit!
"""
    },
    {
        "name": "Sarah",
        "context": "Sarah and her roommate have been living together for 6 months. They have a generally good relationship with clear house rules about cleaning up after meals.",
        "conversation": """
Roommate: Hey Sarah, could you clean your dishes from breakfast?
Sarah: Sure, sorry about that. I was running late for work this morning.
       I'll take care of it when I get home.
"""
    },
    {
        "name": "John",
        "context": "John and his partner have been together for 2 years. John has been stressed at work lately and relies heavily on his morning routine.",
        "conversation": """
Partner: I forgot to pick up milk on the way home.
John: YOU WHAT?! You know I need my morning coffee! 
      This is just like last week when you forgot the laundry detergent! 
      You never think about my needs! This relationship is falling apart!
"""
    }
]

async def run_tests():
    print("Testing overreaction analysis...\n")
    
    for test_case in test_cases:
        print(f"Analyzing case for {test_case['name']}:")
        print("-" * 50)
        print("Context:")
        print(test_case['context'])
        print("\nConversation:")
        print(test_case['conversation'])
        print("-" * 50)
        
        try:
            result = await analyze_overreaction(
                name=test_case['name'],
                context=test_case['context'],
                conversation=test_case['conversation']
            )
            
            print("\nAnalysis Results:")
            print(f"Is overreacting: {result.is_overreacting}")
            print(f"Confidence score: {result.confidence_score}")
            print(f"Emotional state: {result.emotional_state}")
            print("\nExplanation:")
            print(result.explanation)
            print("\nKey triggers:")
            for trigger in result.key_triggers:
                print(f"- {trigger}")
            print("\nSuggested responses:")
            for response in result.suggested_responses:
                print(f"- {response}")
            print("\n" + "="*70 + "\n")
            
        except Exception as e:
            print(f"Error analyzing case: {str(e)}\n")

if __name__ == "__main__":
    asyncio.run(run_tests())