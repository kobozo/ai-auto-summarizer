"""Main functionality for the AI Auto Summarizer."""

import asyncio
import json
from pathlib import Path
import logging

from .core import ContentProcessor
from .core.summarizer import Summarizer

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the AI Auto Summarizer."""
    
    # Load settings from settings.json
    settings_path = Path(__file__).parent / 'settings.json'
    if not settings_path.exists():
        print("Error: settings.json not found. Please copy settings.json.example and configure it.")
        return
    
    with open(settings_path) as f:
        config = json.load(f)
    
    # Initialize processor and summarizer
    processor = ContentProcessor(config)
    summarizer = Summarizer(config)
    
    print("Fetching content from sources...")
    content = await processor.process_sources()
    
    # Count items with transcripts
    items_with_transcript = sum(1 for item in content if item.get('transcript'))
    total_items = len(content)
    logger.info(f"Processing {total_items} items")
    
    # Process transcripts with LLM
    if items_with_transcript > 0:
        print("\nGenerating summaries...")
        content = await summarizer.process_content(content)
        
        # Count successful summaries
        items_with_summary = sum(1 for item in content if item.get('summary'))
        logger.info(f"Generated {items_with_summary} summaries")
    
        # Calculate success rates
        transcript_rate = (items_with_transcript / total_items * 100) if total_items > 0 else 0
        summary_rate = (items_with_transcript / total_items * 100) if total_items > 0 else 0
        
        print(f"\nResults:")
        print(f"Total content items found: {total_items}")
        print(f"Items with transcripts: {items_with_transcript} ({transcript_rate:.1f}%)")
        print(f"Items with summaries: {items_with_summary} ({summary_rate:.1f}%)")
        
        # Print example summary if available
        if content and any(item.get('summary') for item in content):
            example = next(item for item in content if item.get('summary'))
            print(f"\nExample Summary:")
            print(f"Title: {example.get('title', 'Untitled')}")
            print(f"Summary: {example.get('summary')}")
            if example.get('topics'):
                print("\nTopics:")
                for topic in example.get('topics', []):
                    print(f"- {topic.name}: {topic.description}")

if __name__ == "__main__":
    asyncio.run(main())

