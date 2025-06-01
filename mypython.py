import os
import django

from fee_structures_items.models import FeeStructureItem

# Set up Django environment (replace 'your_project.settings' with your actual settings module)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance.settings')
django.setup()


from fee_structures.models import FeeStructure

def delete_fee_structures():
    # Query the FeeStructure records matching the conditions
    fee_structures = FeeStructureItem.objects.filter(
        school_id="9222c6bf-fc87-4008-9b2c-06e500bb93a0",
        id="0660bb24-42b0-4dbc-bc0a-86d0d5d724af"
    )

    # Check if any records exist
    if fee_structures.exists():
        # Delete all matching records
        count = fee_structures.delete()
        print(f"Successfully deleted {count[0]} records.")
    else:
        print("No matching records found.")


# Call the function
delete_fee_structures()