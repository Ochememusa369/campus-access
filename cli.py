import sys
import requests_store
import workflow

def display_menu():
    """Prints a clear, clean visual list of available CLI commands."""
    print("\n=== CAMPUS ACCESS CARD MANAGER ===")
    print("1. Create Request")
    print("2. View Single Request")
    print("3. Approve Request")
    print("4. Issue Card")
    print("5. Return Card")
    print("6. List All Requests")
    print("7. Save to Database (JSON)")
    print("8. Reload from Database (JSON)")
    print("9. Quit Safely")
    print("==================================")

def run_menu():
    """Executes the core application loop, safely catching validation errors."""
    # Define an absolute default persistence path matching challenge rules
    db_filename = "campus_database.json"

    while True:
        display_menu()
        choice = input("Select an option (1-9): ").strip()

        try:
            if choice == "1":
                fellow = input("Enter Fellow ID: ")
                card_type = input("Enter Card Type (visitor/student/staff): ")
                record = requests_store.create_request(fellow, card_type)
                print(f"🎉 Success! Request registered. ID: {record['id']} [Status: {record['status']}]")

            elif choice == "2":
                req_id = input("Enter Request ID (e.g., A001): ").strip().upper()
                record = requests_store.get_request(req_id)
                print(f"\n--- Request Details for {req_id} ---")
                print(f"ID:          {record['id']}")
                print(f"Fellow ID:   {record['fellow_id']}")
                print(f"Card Type:   {record['card_type']}")
                print(f"Status:      {record['status']}")
                print(f"Approved By: {record['approved_by'] or 'None'}")

            elif choice == "3":
                req_id = input("Enter Request ID to Approve: ").strip().upper()
                approver = input("Enter Authorised Staff Approver ID: ")
                workflow.approve_request(req_id, approver)
                print(f"✅ Request {req_id} has been successfully approved by {approver}.")

            elif choice == "4":
                req_id = input("Enter Request ID to Issue: ").strip().upper()
                workflow.issue_card(req_id)
                print(f"🎫 Card for {req_id} has been successfully issued to the fellow.")

            elif choice == "5":
                req_id = input("Enter Request ID to Return: ").strip().upper()
                workflow.return_card(req_id)
                print(f"🛑 Card for {req_id} has been successfully returned and deactivated.")

            elif choice == "6":
                records = requests_store.list_all_requests()
                if not records:
                    print("ℹ️ No active card requests found in memory state.")
                else:
                    print(f"\n{'ID':<6} | {'Fellow ID':<10} | {'Card Type':<10} | {'Status':<10} | {'Approver'}")
                    print("-" * 55)
                    for r in records:
                        print(f"{r['id']:<6} | {r['fellow_id']:<10} | {r['card_type']:<10} | {r['status']:<10} | {r['approved_by']}")

            elif choice == "7":
                requests_store.save_requests(db_filename)
                print(f"💾 Memory states securely saved to local storage file: '{db_filename}'")

            elif choice == "8":
                requests_store.load_requests(db_filename)
                print(f"🔄 Database data reloaded successfully into memory from: '{db_filename}'")

            elif choice == "9":
                print("👋 Exiting system safely. Goodbye!")
                break

            else:
                # Case 8 Checkpoint: Gives helpful feedback on an invalid index or typo
                print("❌ Invalid menu option selection. Please enter a valid number from 1 to 9.")

        except (ValueError, RuntimeError) as err:
            # Captures business logic exceptions and keeps the loop spinning
            print(f"⚠️ Operation Rejected: {err}")
        except KeyError as err:
            print(f"⚠️ Operation Rejected: Database record key not found. {err}")






