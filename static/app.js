const rows = document.querySelector("#student-rows");
const searchInput = document.querySelector("#search");
const statusFilter = document.querySelector("#status-filter");
const dialog = document.querySelector("#student-dialog");
const form = document.querySelector("#student-form");
const formError = document.querySelector("#form-error");
const pageSize = 8;
let students = [];
let currentPage = 1;
let toastTimer;

document.querySelector("#today").textContent = new Intl.DateTimeFormat("en", {
  weekday: "short", month: "short", day: "numeric",
}).format(new Date());
document.querySelector("#current-year").textContent = new Date().getFullYear();

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join(", ") : detail || "Request failed");
  }
  return response.status === 204 ? null : response.json();
}

function initials(name) {
  return name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function renderStudents() {
  const query = searchInput.value.trim().toLowerCase();
  const status = statusFilter.value;
  const visible = students.filter((student) => {
    const matchesText = [student.full_name, student.roll_number, student.email, student.course]
      .some((value) => value.toLowerCase().includes(query));
    return matchesText && (status === "All" || student.status === status);
  });
  const pageCount = Math.max(1, Math.ceil(visible.length / pageSize));
  currentPage = Math.min(currentPage, pageCount);
  const start = (currentPage - 1) * pageSize;
  const pageStudents = visible.slice(start, start + pageSize);

  rows.innerHTML = pageStudents.map((student) => `
    <tr>
      <td><div class="student-cell"><div class="student-avatar">${escapeHtml(initials(student.full_name))}</div>
        <div><div class="student-name">${escapeHtml(student.full_name)}</div><div class="student-email">${escapeHtml(student.email)}</div></div></div></td>
      <td><span class="roll-number">${escapeHtml(student.roll_number)}</span></td>
      <td>${escapeHtml(student.course)}</td><td>Year ${student.year}</td>
      <td><span class="status-badge ${student.status === "Active" ? "status-active" : "status-inactive"}">${student.status}</span></td>
      <td><div class="row-actions"><button data-action="edit" data-id="${student.id}">Edit</button><button class="delete-action" data-action="delete" data-id="${student.id}">Delete</button></div></td>
    </tr>`).join("");

  document.querySelector("#visible-count").textContent = visible.length;
  document.querySelector("#page-summary").textContent = visible.length
    ? `Showing ${start + 1}–${Math.min(start + pageSize, visible.length)} of ${visible.length} students`
    : "Showing 0 students";
  document.querySelector("#page-number").textContent = `${currentPage} / ${pageCount}`;
  document.querySelector("#previous-page").disabled = currentPage === 1;
  document.querySelector("#next-page").disabled = currentPage === pageCount;
  document.querySelector("#empty-state").classList.toggle("visible", visible.length === 0);
}

async function refresh() {
  document.querySelector("#error-state").hidden = true;
  try {
    const [studentData, stats] = await Promise.all([api("/api/students"), api("/api/stats")]);
    students = studentData;
    currentPage = 1;
    document.querySelector("#total-count").textContent = stats.total;
    document.querySelector("#active-count").textContent = stats.active;
    document.querySelector("#course-count").textContent = stats.courses;
    renderStudents();
  } catch (error) {
    document.querySelector("#error-state").hidden = false;
    document.querySelector("#empty-state").classList.remove("visible");
    showToast(error.message);
  }
}

function showToast(message) {
  const toast = document.querySelector("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2800);
}

function openDialog(student = null) {
  form.reset();
  formError.textContent = "";
  document.querySelector("#student-id").value = student?.id ?? "";
  document.querySelector("#dialog-title").textContent = student ? "Edit student" : "Add student";
  document.querySelector("#save-student").textContent = student ? "Save changes" : "Save student";
  if (student) {
    for (const field of ["roll_number", "full_name", "email", "course", "year", "status"]) {
      document.querySelector(`#${field.replaceAll("_", "-")}`).value = student[field];
    }
  }
  dialog.showModal();
}

document.querySelector("#add-student").addEventListener("click", () => openDialog());
document.querySelector("#empty-add").addEventListener("click", () => openDialog());
document.querySelector("#close-dialog").addEventListener("click", () => dialog.close());
document.querySelector("#cancel-dialog").addEventListener("click", () => dialog.close());
document.querySelector("#retry").addEventListener("click", refresh);
searchInput.addEventListener("input", () => {
  currentPage = 1;
  renderStudents();
});
statusFilter.addEventListener("change", () => {
  currentPage = 1;
  document.querySelector("#filter-label").textContent = statusFilter.value === "All" ? "All students" : statusFilter.value;
  renderStudents();
});
document.querySelector("#previous-page").addEventListener("click", () => {
  currentPage -= 1;
  renderStudents();
});
document.querySelector("#next-page").addEventListener("click", () => {
  currentPage += 1;
  renderStudents();
});
document.querySelector("#filter-button").addEventListener("click", () => {
  const options = [...statusFilter.options].map((option) => option.value);
  const next = options[(options.indexOf(statusFilter.value) + 1) % options.length];
  statusFilter.value = next;
  statusFilter.dispatchEvent(new Event("change"));
});
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    searchInput.focus();
  }
});

rows.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const student = students.find((item) => item.id === Number(button.dataset.id));
  if (!student) return;
  if (button.dataset.action === "edit") {
    openDialog(student);
    return;
  }
  if (!window.confirm(`Delete ${student.full_name}'s record? This cannot be undone.`)) return;
  try {
    await api(`/api/students/${student.id}`, { method: "DELETE" });
    showToast("Student record deleted.");
    await refresh();
  } catch (error) {
    showToast(error.message);
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  formError.textContent = "";
  const id = document.querySelector("#student-id").value;
  const student = {
    roll_number: document.querySelector("#roll-number").value.trim(),
    full_name: document.querySelector("#full-name").value.trim(),
    email: document.querySelector("#email").value.trim(),
    course: document.querySelector("#course").value.trim(),
    year: Number(document.querySelector("#year").value),
    status: document.querySelector("#status").value,
  };
  const button = document.querySelector("#save-student");
  button.disabled = true;
  try {
    await api(id ? `/api/students/${id}` : "/api/students", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(student),
    });
    dialog.close();
    showToast(id ? "Student record updated." : "Student added successfully.");
    await refresh();
  } catch (error) {
    formError.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

refresh();
