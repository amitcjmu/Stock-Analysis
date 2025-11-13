"""
Script to regenerate questionnaire with MCQ format for a collection flow.
Run this after deleting old questionnaires to get the new MCQ format.
"""

import asyncio
import sys
from uuid import UUID
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.collection_flow.collection_flow_model import CollectionFlow
from app.services.collection.gap_scanner.gap_detector import GapDetector
from app.services.ai_analysis.questionnaire_generator.service.core import (
    QuestionnaireGeneratorService,
)
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def regenerate_questionnaire(flow_id: str):
    """Regenerate questionnaire for a collection flow."""

    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Get the flow
            result = await session.execute(
                select(CollectionFlow).where(CollectionFlow.flow_id == UUID(flow_id))
            )
            flow = result.scalar_one_or_none()

            if not flow:
                logger.error(f"Flow not found: {flow_id}")
                return False

            logger.info(f"✓ Flow found: {flow.flow_id}")
            logger.info(f"  Current phase: {flow.current_phase}")
            logger.info(f"  Status: {flow.status}")

            # Get the asset ID from metadata
            selected_assets = flow.metadata.get("selected_asset_ids", [])
            logger.info(f"  Selected assets: {selected_assets}")

            if not selected_assets:
                logger.error("No assets selected in flow metadata")
                return False

            # Initialize services
            gap_detector = GapDetector(session)
            questionnaire_service = QuestionnaireGeneratorService(session)

            # Detect gaps for the asset
            logger.info("\nDetecting gaps...")
            gaps = await gap_detector.detect_gaps(
                client_account_id=flow.client_account_id,
                engagement_id=flow.engagement_id,
                asset_ids=selected_assets,
            )

            logger.info(f"✓ Detected {len(gaps)} gaps")

            # Generate questionnaire
            logger.info("\nGenerating questionnaire with MCQ format...")
            questionnaire = await questionnaire_service.generate_questionnaire(
                client_account_id=flow.client_account_id,
                engagement_id=flow.engagement_id,
                collection_flow_id=flow.flow_id,
                gaps=gaps,
                use_agent_generation=True,
            )

            logger.info("\n✓ Questionnaire generated successfully!")
            logger.info(f"  ID: {questionnaire.id}")
            logger.info(f"  Total questions: {len(questionnaire.questions)}")

            # Analyze question types
            mcq_count = sum(
                1
                for q in questionnaire.questions
                if q.get("field_type") in ("select", "multiselect", "radio")
            )
            non_mcq_count = len(questionnaire.questions) - mcq_count

            logger.info("\nQuestion Type Distribution:")
            logger.info(f"  MCQ questions (select/multiselect/radio): {mcq_count}")
            logger.info(f"  Non-MCQ questions: {non_mcq_count}")

            # Show first 5 questions
            logger.info("\nFirst 5 Questions:")
            for i, q in enumerate(questionnaire.questions[:5], 1):
                logger.info(f"\n  Question {i}:")
                logger.info(f'    ID: {q.get("field_id")}')
                logger.info(f'    Text: {q.get("question_text")[:60]}...')
                logger.info(f'    Type: {q.get("field_type")}')
                logger.info(f'    Category: {q.get("category")}')
                if q.get("options"):
                    logger.info(f'    Options: {len(q.get("options", []))} choices')

            return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python regenerate_questionnaire.py <flow_id>")
        print(
            "Example: python regenerate_questionnaire.py b7ba1f33-c463-4962-9c0b-6295effd224b"
        )
        sys.exit(1)

    flow_id = sys.argv[1]
    success = asyncio.run(regenerate_questionnaire(flow_id))

    if success:
        print("\n✓ Questionnaire regeneration completed successfully!")
        print("\nNext steps:")
        print(f"1. Open http://localhost:8081/collection/flows/{flow_id}")
        print("2. Verify all questions are in MCQ format")
        print("3. Test question 5 displays correctly")
        print("4. Submit the form and verify data persistence")
    else:
        print("\n✗ Questionnaire regeneration failed!")
        sys.exit(1)
