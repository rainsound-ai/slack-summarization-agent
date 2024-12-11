from notion_client import NotionClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_notion_integration():
    try:
        client = NotionClient()
        
        # Step 1: Create button property in the database
        logger.info("Creating button property...")
        if not client.create_button_property(client.subprojects_db_id):
            raise Exception("Failed to create button property")
            
        # Step 2: Set up webhook integration
        logger.info("Setting up webhook integration...")
        if not client.setup_webhook_integration():
            raise Exception("Failed to set up webhook integration")
            
        logger.info("Notion integration setup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Go to your Notion database")
        logger.info("2. You should see a new 'Test Button' property")
        logger.info("3. Start the webhook server: python webhook_server.py")
        logger.info("4. Click the button in Notion to test the integration")
        
    except Exception as e:
        logger.error(f"Error setting up Notion integration: {e}")
        raise

if __name__ == "__main__":
    setup_notion_integration() 