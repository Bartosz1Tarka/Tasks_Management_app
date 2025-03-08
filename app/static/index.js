// Funkcja do uuwania notatek
function deleteNote(noteId) {    //wywołanie funkcji (gdy button z atrybutem onClick="deleteNote({{ note.id }})" jest wciśniety)
  fetch("/delete-note", {        //wysłanie żądania (fetch) do do serwera (Flaskowego)
    method: "POST",              //metoda: POST, a więc chcemy przesłać dane do serwera
    body: JSON.stringify({ noteId: noteId }), //parsowanie zawartości requesta na JSON i dołącza je do żądania wysyłanego na serwer
  }).then((_res) => {             //jeżeli backend odpowie (może być to np. pusty JSON, jak w tym przypadku)
    window.location.href = "/";   //przejdź na stronę główną (refresh)
  });
}


// OBSŁUGA MODALA
$(document).ready(function() { // Dodaj to, aby upewnić się, że kod działa po załadowaniu DOM
  $('#edit-button').on('show.bs.modal', function (event) {
      var button = $(event.relatedTarget); // Przycisk, który wywołał modal
      var title = button.data('title'); // Pobierz tytuł z atrybutu data-title
      var body = button.data('body')
      var modal = $(this);
      modal.find('.modal-title').text(title); // Ustaw tytuł modala
      modal.find('.modal-body').text(body);
  });
});

//WYPEŁNIENIE MODALA TREŚCIĄ 
function fillModal(noteId) {

  fetch("/fill-modal", {
    method: "POST",
    body: JSON.stringify({ noteId: noteId }),
  })

  .then(response => response.json())
  .then(data => {
    document.getElementById(`edit-title-${noteId}`).value = data.title;
    document.getElementById(`edit-note-${noteId}`).value = data.body;
    document.getElementById(`edit-date-${noteId}`).value = data.deadline;
    document.getElementById(`edit-status-${noteId}`).value = data.status;
  })
.catch(error => console.error("Error fetching note:", error));
}