// document.querySelectorAll('.expandable-textarea').forEach(textarea => {
//     // Initially adjust the height to fit the content
//     textarea.style.height = 'auto';
//     textarea.style.height = `${textarea.scrollHeight}px`;

//     textarea.addEventListener('input', () => {
//         // Reset height to auto to shrink if necessary
//         textarea.style.height = 'auto';
//         // Adjust height to fit the new content
//         textarea.style.height = `${textarea.scrollHeight}px`;
//     });
// });


function toggleEditForm(button) {
    const container = button.closest('.editable-field');
    const staticValue = container.querySelector('.static-value');
    const form = container.querySelector('.edit-form');

    // Toggle visibility
    staticValue.classList.add('hidden');
    button.classList.add('hidden');
    form.classList.remove('hidden');
}

function cancelEdit(button) {
    const container = button.closest('.editable-field');
    const staticValue = container.querySelector('.static-value');
    const form = container.querySelector('.edit-form');
    const editButton = container.querySelector('.edit-button');

    // Revert visibility
    staticValue.classList.remove('hidden');
    form.classList.add('hidden');
    editButton.classList.remove('hidden');
}
