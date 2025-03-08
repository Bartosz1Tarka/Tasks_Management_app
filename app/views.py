from flask import Blueprint, render_template, request, redirect, flash, jsonify
from flask_login import login_required, current_user
from .models import Note, Tag, Status
from . import db
import json
from datetime import datetime

views = Blueprint('views', __name__)

def valid_task_data(reqest):
 
    #pobranie danych z formularzy
    title = request.form.get('title')
    note = request.form.get('note')
    plain_deadline = request.form.get('deadline')
    status_name = request.form.get('status')
    tags = request.form.getlist('tags')


    #walidacja danych
    if len(note) <= 1:
        flash('Note is too short. You have to input minimum 2 characters.', category="error")
    elif len(title) == 0:
        flash('"Title" field can not be empty.', category="error")
    elif len(note) > 1000:
        flash('Note is too long. Maximum lenght is up to 1000 characters.', category="error")
    elif len(title) > 150:
        flash('Title is to long. Maximum lenght is up to 150 characters.', category="error")
    elif not tags:
        flash('"Tag" field cannot be empty.', category="error")
    elif not status_name:
        status_name = "Not assigned"
    
    else:

        if not plain_deadline.strip():
            deadline_object = datetime.now().date()
        else:
            deadline_object = datetime.strptime(plain_deadline, "%Y-%m-%d").date()

        status_object = Status.query.filter_by(name=status_name).first()
        if not status_object:
            flash('Invalid Status object.', category="error")
            return redirect(request.url)
        else:
            status_id = status_object.id
        

        return {
            "success": True,
            "data": {"title": title, "note": note, "deadline": deadline_object, "status_id": status_id, "tags": tags}
        }

#STRONA GŁÓWNA
@views.route('/', methods=["GET", "POST"])
@login_required
def tasks_management():

    if request.method == "POST":            
        result = valid_task_data(request)

        if result.get("success"): 

            tag_list = result["data"]["tags"]

            new_note = Note(
                title=result["data"]["title"],
                data=result["data"]["note"],
                deadline=result["data"]["deadline"],
                status_id=result["data"]["status_id"],
                user_id=current_user.id, 
            ) #utworzenie nowej instancji klasy Note (notatki w RAM)
            
           
            # Przypisanie tagu do notatki
            for tag_name in tag_list:
                tag = Tag.query.filter_by(name=tag_name).first()
                new_note.tags.append(tag)

            #Zapis notatki do bazy danych
            db.session.add(new_note)
            db.session.commit() #zatwierdzenie zmian
            flash("Note added.", category="success")
    
        else:
            flash("Check provided task data and retry.", category="error")
            
    #Dynamiczne obliczanie pozostałego czasu - dodanie atrybutu remain_time do notatki
    for note in current_user.notes:
        time_difference = (note.deadline - datetime.now()).total_seconds()

        if time_difference > 0:
            if time_difference < 86400:
                remain_hours = time_difference / 3600
                note.remain_time = f"{remain_hours:.0f} hours left"
            else:
                remain_days = time_difference / 86400
                note.remain_time = f"{remain_days:.0f} days left"
        else:
            if time_difference > -86400:
                remain_hours = (time_difference / 3600) * (-1)
                note.remain_time = f"{remain_hours:.0f} hours overdue"
            else:
                remain_days = (time_difference / 86400) * (-1)
                note.remain_time = f"{remain_days:.0f} days overdue"
                


    tags_list = Tag.query.all() #pobierz wszystkie tagi z bazy danych, aby później przesłać je do przeglądarki
    statuses_list = Status.query.all() #to samo ze statusami

    #wyświetlenie podstrony w przeglądarce
    return render_template("home.html", user=current_user, tags=tags_list, statuses=statuses_list, notes=current_user.notes)

"""

#FUNKCJA ZAPISUJĄCA ZMIANY PODCZAS EDYCJI W MODALU
@views.route('/edit-note', methods=["PUT"])
@login_required
def edit_task(note_id):
    if request.method == "PUT":
        result = valid_task_data(request)

        if result["success"] == True:

            note_to_update = Note.query.filter_by(id=note_id, user_id=current_user).first()

            if note_to_update:

                    note_to_update.title = result["data"]["title"]
                    note_to_update.data = result["data"]["note"]
                    note_to_update.deadline = result["data"]["deadline"]
                    note_to_update.status_id = result["data"]["status_id"]
                
                    if note_to_update.tags:
                        note_to_update.tags.clear()
                


            else:
                flash(f"Can not find task. Please try to open 'Task Properties' once again and retry to update.", category="error")

"""

        
#FUNKCJA USUWANIA NOTATEK
@views.route('/delete-note', methods=["POST"])
def delete_note():
    #Usunięcie notatki na podstawie ID przesłanego w żądaniu POST.
    note = json.loads(request.data) #Załadowanie danych JSON z żądania. Prop. zmiany=> note = request.get_json()
    noteId = note['noteId'] #Pobranie ID notatki z danych JSON
    note = Note.query.get(noteId) #Wyszukanie notatki w bazie danych
    if note: #Sprawdzenie, czy notatka istnieje
        if note.user_id == current_user.id: #Sprawdzenie, czy użytkownik jest właścicielem notatki
            db.session.delete(note) #Usunięcie notatki z sesji
            db.session.commit() #Zatwierdzenie zmian w bazie danych
            
    return jsonify([]) #Zwrócenie pustego JSON jako odpowiedź



#FUNKCJA DYNAMICZNEGO ODCZYTYWANIA TREŚCI NOTATKI PRZEZ MODAL
@views.route('/fill-modal', methods=["POST"])
def fill_modal():

    note = json.loads(request.data)

    noteId = note['noteId']

    note = Note.query.get(noteId)

    if not note:
        print(f"Błąd. Notakta o ID {noteId} nie została znaleziona w bazie.")
        return jsonify({"error": "Note not found"}), 404

    return jsonify({
        "id": note.id,
        "title": note.title,
        "body": note.data,
        "deadline": note.deadline.strftime("%Y-%m-%d") if note.deadline else None,
        "status": note.status.name,
        "tags": [tag.name for tag in note.tags]
    })


#FUNKCJA DODAWANIA I USUWANIA TAGÓW DO BAZY DANYCH
@views.route('/new-tag', methods=["GET", "POST"])
@views.route('/remove-tag', methods=["POST"])
@login_required
def add_tag():
    if request.method == "POST":
        #DODAWANIE NOWEGO TAGU
        if request.path == "/new-tag":
            if 'new_tag' in request.form:
                tag = request.form.get('new_tag')
                color = request.form.get('tag_color')

                if len(tag) < 2 or len(tag) > 50:
                    flash("Tag name lenght is invalid. It should be in range 2-50 characters.", category='error')
                elif color[0] != "#" and len(color) != 7:
                    flash("Wrong color data.", category='error')
                else:
                    new_tag = Tag(name=tag, color=color)
                    db.session.add(new_tag)
                    db.session.commit()
                    flash("New tag added successfuly!")
        #USUWANIE TAGÓW
        if request.path == "/remove-tag":
        
            if 'removed_tags' in request.form:
                removed_tags = request.form.getlist('removed_tags')

                if len(removed_tags) < 1:
                    flash("Please choose a tag to remove.", category='error')
                else:
                    for tag in removed_tags:
                        tag_to_remove = Tag.query.filter_by(name=tag).first()
                        if tag_to_remove:
                            db.session.delete(tag_to_remove)
                            flash(f"Tag {tag_to_remove.name} was successfuly removed.", category='success')
                        else:
                            flash(f"Tag {tag} is not existing!", category='error')

                    db.session.commit()
        
    current_tags = Tag.query.all()
    current_statuses = Status.query.all()
        
    return render_template("new_tag.html", user=current_user, tags=current_tags, statuses=current_statuses)

#FUNKCJA DODAWANIA I USUWANIA STATUSÓW DO BAZY DANYCH
@views.route('/new-status', methods=["POST", "GET"])
@views.route('/remove-status', methods=["POST"])
@login_required
def add_status():
    if request.method == "POST":
        #DODAWANIE NOWEGO STATUSU
        if request.path == '/new-status':
            if 'new_status' in request.form:
                new_status = request.form.get('new_status')
                status_color = request.form.get('status_color')

                if len(new_status) < 2 or len(new_status) > 50:
                    flash("Status name lenght is invalid. It should be in range 2-50 characters.", category='error')
                else:
                    if status_color[0] != "#" or len(status_color) != 7:
                        new_status = Status(name=new_status)
                        db.session.add(new_status)
                        db.session.commit()
                        flash("New status added successfuly.")
                    else:
                        new_status = Status(name=new_status, color=status_color)
                        db.session.add(new_status)
                        db.session.commit()
                        flash("New status added successfuly.")

        #USUWANIE STATUSÓW
        if request.path == '/remove-status':

            if 'removed_statuses' in request.form:
                removed_statuses = request.form.getlist('removed_statuses')
                if len(removed_statuses) < 1:
                    flash("Please choose the status to remove.", category='error')
                else:
                    for status in removed_statuses:
                        status_to_remove = Status.query.filter_by(name=status).first()
                        if status_to_remove:
                            db.session.delete(status_to_remove)
                            flash(f"Status {status_to_remove.name} was successfuly removed.", category='success')
                        else:
                            flash(f"Status {status} does not exist in database.", category='error')

                db.session.commit()
        
        current_statuses = Status.query.all()
        current_tags = Tag.query.all()
            
    return render_template("new_tag.html", user=current_user, statuses=current_statuses, tags=current_tags)