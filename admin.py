import json
import sys
import uuid

PERSONNEL_FILE = "personnel.json"
HOLIDAYS_FILE = "holidays.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def list_personnel():
    data = load_json(PERSONNEL_FILE)
    for p in data["personnel"]:
        status = "Active" if p["isActive"] else "Inactive"
        print(f"{p['id']}: {p['name']} <{p['email']}> [{status}]")

def add_person(name, email):
    data = load_json(PERSONNEL_FILE)
    new_id = str(uuid.uuid4())
    data["personnel"].append({"id": new_id, "name": name, "email": email, "isActive": True})
    save_json(PERSONNEL_FILE, data)
    print(f"Added: {name} <{email}>")

def edit_person(pid, name=None, email=None, isActive=None):
    data = load_json(PERSONNEL_FILE)
    for p in data["personnel"]:
        if p["id"] == pid:
            if name: p["name"] = name
            if email: p["email"] = email
            if isActive is not None: p["isActive"] = isActive
            save_json(PERSONNEL_FILE, data)
            print(f"Updated: {p['name']} <{p['email']}> [{p['isActive']}]")
            return
    print("Person not found.")

def remove_person(pid):
    data = load_json(PERSONNEL_FILE)
    data["personnel"] = [p for p in data["personnel"] if p["id"] != pid]
    save_json(PERSONNEL_FILE, data)
    print(f"Removed person with id {pid}")

def list_holidays():
    data = load_json(HOLIDAYS_FILE)
    for h in data["holidays"]:
        print(f"{h['date']}: {h['name']}")

def add_holiday(date, name):
    data = load_json(HOLIDAYS_FILE)
    data["holidays"].append({"date": date, "name": name})
    save_json(HOLIDAYS_FILE, data)
    print(f"Added holiday: {date} - {name}")

def remove_holiday(date):
    data = load_json(HOLIDAYS_FILE)
    data["holidays"] = [h for h in data["holidays"] if h["date"] != date]
    save_json(HOLIDAYS_FILE, data)
    print(f"Removed holiday on {date}")

def usage():
    print("""
Admin Commands:
  python admin.py list-personnel
  python admin.py add-person "Name" "email@example.com"
  python admin.py edit-person <id> [--name "New Name"] [--email "new@email.com"] [--active true|false]
  python admin.py remove-person <id>
  python admin.py list-holidays
  python admin.py add-holiday YYYY-MM-DD "Holiday Name"
  python admin.py remove-holiday YYYY-MM-DD
  python admin.py pause-order
  python admin.py resume-order
  python admin.py reset-order
""")

def main():
    if len(sys.argv) < 2:
        usage()
        return
    cmd = sys.argv[1]
    if cmd == "list-personnel":
        list_personnel()
    elif cmd == "add-person" and len(sys.argv) == 4:
        add_person(sys.argv[2], sys.argv[3])
    elif cmd == "edit-person" and len(sys.argv) >= 3:
        pid = sys.argv[2]
        name = None
        email = None
        isActive = None
        for i, arg in enumerate(sys.argv):
            if arg == "--name" and i+1 < len(sys.argv):
                name = sys.argv[i+1]
            if arg == "--email" and i+1 < len(sys.argv):
                email = sys.argv[i+1]
            if arg == "--active" and i+1 < len(sys.argv):
                isActive = sys.argv[i+1].lower() == "true"
        edit_person(pid, name, email, isActive)
    elif cmd == "remove-person" and len(sys.argv) == 3:
        remove_person(sys.argv[2])
    elif cmd == "list-holidays":
        list_holidays()
    elif cmd == "add-holiday" and len(sys.argv) == 4:
        add_holiday(sys.argv[2], sys.argv[3])
    elif cmd == "remove-holiday" and len(sys.argv) == 3:
        remove_holiday(sys.argv[2])
    elif cmd == "pause-order":
        settings = load_json("settings.json")
        settings["paused"] = True
        save_json("settings.json", settings)
        print("Order paused. Scheduling will not advance.")
    elif cmd == "resume-order":
        settings = load_json("settings.json")
        settings["paused"] = False
        save_json("settings.json", settings)
        print("Order resumed. Scheduling will advance as normal.")
    elif cmd == "reset-order":
        settings = load_json("settings.json")
        settings["custom_order"] = []
        save_json("settings.json", settings)
        print("Order reset to default alphabetical order.")
    else:
        usage()

if __name__ == "__main__":
    main()
