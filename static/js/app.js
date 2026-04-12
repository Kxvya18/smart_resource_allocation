function getCsrfToken() {
    const cookieValue = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrftoken="));
    return cookieValue ? cookieValue.split("=")[1] : "";
}

function renderResourceCard(resource, isManager) {
    const statusClass =
        resource.status === "active"
            ? "text-bg-success"
            : resource.status === "maintenance"
                ? "text-bg-warning"
                : "text-bg-secondary";
    const editButton = isManager
        ? `<a class="btn btn-outline-dark btn-sm" href="/resources/${resource.id}/edit/">Edit</a>`
        : "";
    const sourceLink = resource.source_url
        ? `<p class="small mt-2 mb-2"><a href="${resource.source_url}" target="_blank" rel="noopener noreferrer">Source: ${resource.source_name || "Official reference"}</a></p>`
        : "";

    return `
        <div class="col-lg-4">
            <div class="resource-card">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <span class="badge text-bg-info text-capitalize">${resource.resource_type_label}</span>
                        <h2 class="h5 mt-2 mb-1">${resource.name}</h2>
                        <p class="small text-secondary mb-0">${resource.building}${resource.location_detail ? `, ${resource.location_detail}` : ""}</p>
                    </div>
                    <span class="badge ${statusClass}">${resource.status_label}</span>
                </div>
                <p>${resource.description || "No description provided."}</p>
                <div class="resource-meta">
                    <span>Capacity: ${resource.capacity}</span>
                    <span>${resource.available_from.slice(0, 5)} - ${resource.available_until.slice(0, 5)}</span>
                </div>
                ${sourceLink}
                <p class="small text-secondary mt-3 mb-3">${resource.features || ""}</p>
                <div class="d-flex gap-2">
                    <a class="btn btn-primary btn-sm" href="/resources/${resource.id}/">View</a>
                    <a class="btn btn-outline-primary btn-sm" href="/bookings/new/?resource=${resource.id}">Book</a>
                    ${editButton}
                </div>
            </div>
        </div>
    `;
}

function renderTopResource(resource) {
    const source = resource.source_url
        ? `<a href="${resource.source_url}" target="_blank" rel="noopener noreferrer" class="small">Source</a>`
        : "";
    return `
        <div class="rank-item">
            <div>
                <strong>${resource.name}</strong>
                <div class="small text-secondary">${resource.resource_type} • ${resource.building}</div>
                ${source}
            </div>
            <div class="text-end">
                <div class="fw-semibold">${resource.hours} hrs</div>
                <div class="small text-secondary">${resource.utilization}% util. • ${resource.bookings} bookings</div>
            </div>
        </div>
    `;
}

function renderScheduleItem(item, showUser) {
    const userLine = showUser ? ` by ${item.user_name}` : "";
    return `
        <div class="timeline-item">
            <div>
                <strong>${item.title}</strong>
                <div class="small text-secondary">${item.resource_name}${userLine}</div>
            </div>
            <div class="text-end">
                <div class="fw-semibold">${item.start}</div>
                <div class="small text-secondary text-capitalize">${item.status_label}</div>
            </div>
        </div>
    `;
}

function renderActivityItem(item) {
    return `
        <div class="activity-item">
            <strong>${item.title}</strong>
            <div class="small text-secondary">${item.resource_name} • ${item.status_label} • ${item.updated_at}</div>
        </div>
    `;
}

function renderMaintenanceItem(item) {
    return `<div class="mini-chip">${item.name}</div>`;
}

function fallbackMarkup(message) {
    return `<div class="small text-secondary">${message}</div>`;
}

function parseDateTimeLocal(value) {
    if (!value) {
        return null;
    }
    return new Date(value);
}

function formatDateTimeLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function formatCurrency(amount) {
    return `Rs. ${Number(amount).toFixed(2)}`;
}

function roundToNextHalfHour(date) {
    const rounded = new Date(date.getTime());
    rounded.setSeconds(0, 0);
    const minutes = rounded.getMinutes();
    if (minutes === 0 || minutes === 30) {
        return rounded;
    }
    if (minutes < 30) {
        rounded.setMinutes(30);
        return rounded;
    }
    rounded.setHours(rounded.getHours() + 1);
    rounded.setMinutes(0);
    return rounded;
}

function enforceBookingWindow(input, isEndField) {
    const value = parseDateTimeLocal(input.val());
    if (!value) {
        return;
    }
    const now = new Date();
    now.setSeconds(0, 0);
    const adjusted = new Date(value.getTime());
    let changed = false;

    if (adjusted < now) {
        adjusted.setTime(now.getTime());
        changed = true;
    }
    if (adjusted.getHours() < 9) {
        adjusted.setHours(9, 0, 0, 0);
        changed = true;
    }
    if (adjusted.getHours() > 21 || (adjusted.getHours() === 21 && adjusted.getMinutes() > 0)) {
        adjusted.setHours(isEndField ? 21 : 20, isEndField ? 0 : 30, 0, 0);
        changed = true;
    }
    if (changed) {
        input.val(formatDateTimeLocal(adjusted));
    }
}

function updateBookingPreview(form) {
    const resourceCostMapNode = document.getElementById("resource-cost-map");
    const resourceCostMap = resourceCostMapNode ? JSON.parse(resourceCostMapNode.textContent) : {};
    const resourceId = form.find("#id_resource").val();
    const resourceCost = Number(resourceCostMap[resourceId] || 0);
    const start = parseDateTimeLocal(form.find("#id_requested_start").val());
    const end = parseDateTimeLocal(form.find("#id_requested_end").val());

    if (!start || !end || end <= start) {
        $("#booking-duration").text("Select a valid time range");
        $("#booking-cost").text("Select a resource and time slot");
        return;
    }

    const durationHours = (end - start) / (1000 * 60 * 60);
    $("#booking-duration").text(`${durationHours.toFixed(1)} hours`);
    $("#booking-cost").text(formatCurrency(durationHours * resourceCost));
}

function renderSuggestions(data) {
    if (!data.suggestions || !data.suggestions.length) {
        return "No alternate slots found in the immediate search window.";
    }
    const suggestionItems = data.suggestions
        .map(
            (slot) => `
                <button
                    type="button"
                    class="suggested-slot"
                    data-start="${slot.start_value}"
                    data-end="${slot.end_value}"
                >
                    <strong>${slot.start}</strong>
                    <span>to ${slot.end}</span>
                </button>
            `
        )
        .join("");
    return `<div class="mb-2"><strong>Suggested next slots:</strong></div><div class="suggested-slot-list">${suggestionItems}</div>`;
}

let bookingTrendChart;
let bookingStatusChart;
let resourceTypeChart;

function upsertChart(chartRef, canvasId, config) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        return chartRef;
    }
    if (chartRef) {
        chartRef.data = config.data;
        chartRef.options = config.options;
        chartRef.update();
        return chartRef;
    }
    return new Chart(ctx, config);
}

function updateDashboard(data) {
    $("#summary-sources-backed").text(data.totals.sources_backed);
    $("#summary-active-resources").text(data.totals.active_resources);
    $("#summary-pending-bookings").text(data.totals.pending_requests);
    $("#summary-today-load").text(data.totals.today_load);
    $("#metric-bookings-window").text(data.totals.bookings_in_window);
    $("#metric-utilization").text(`${data.totals.utilization_rate}%`);
    $("#metric-approval").text(`${data.totals.approval_rate}%`);
    $("#metric-fill-rate").text(`${data.totals.average_fill_rate}%`);

    bookingTrendChart = upsertChart(bookingTrendChart, "bookingTrendChart", {
        type: "line",
        data: {
            labels: data.daily_bookings.map((item) => item.date),
            datasets: [
                {
                    label: "Total",
                    data: data.daily_bookings.map((item) => item.total),
                    borderColor: "#123458",
                    backgroundColor: "rgba(18, 52, 88, 0.15)",
                    fill: true,
                    tension: 0.3,
                },
                {
                    label: "Pending",
                    data: data.daily_bookings.map((item) => item.pending),
                    borderColor: "#d18b00",
                    backgroundColor: "rgba(209, 139, 0, 0.10)",
                    tension: 0.3,
                },
                {
                    label: "Completed",
                    data: data.daily_bookings.map((item) => item.completed),
                    borderColor: "#2f7f80",
                    backgroundColor: "rgba(47, 127, 128, 0.10)",
                    tension: 0.3,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: "top" } },
        },
    });

    bookingStatusChart = upsertChart(bookingStatusChart, "bookingStatusChart", {
        type: "doughnut",
        data: {
            labels: data.status_counts.map((item) => item.label),
            datasets: [
                {
                    data: data.status_counts.map((item) => item.value),
                    backgroundColor: ["#123458", "#2f7f80", "#e9b949", "#d66c4a", "#9aa5b1"],
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: "bottom" } },
        },
    });

    resourceTypeChart = upsertChart(resourceTypeChart, "resourceTypeChart", {
        type: "bar",
        data: {
            labels: data.type_counts.map((item) => item.label),
            datasets: [
                {
                    label: "Resources",
                    data: data.type_counts.map((item) => item.value),
                    backgroundColor: ["#123458", "#2f7f80", "#e9b949"],
                    borderRadius: 8,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
        },
    });

    $("#top-resource-list").html(
        data.top_resources.length ? data.top_resources.map(renderTopResource).join("") : fallbackMarkup("No recent utilization data.")
    );
    $("#today-schedule-list").html(
        data.today_schedule.length ? data.today_schedule.map((item) => renderScheduleItem(item, false)).join("") : fallbackMarkup("No bookings scheduled for today.")
    );
    $("#pending-queue-list").html(
        data.pending_queue.length ? data.pending_queue.map((item) => renderScheduleItem(item, true)).join("") : fallbackMarkup("No pending approvals right now.")
    );
    $("#recent-activity-list").html(
        data.recent_activity.length ? data.recent_activity.map(renderActivityItem).join("") : fallbackMarkup("No recent activity yet.")
    );
    $("#maintenance-list").html(
        data.maintenance_resources.length ? data.maintenance_resources.map(renderMaintenanceItem).join("") : fallbackMarkup("No resources in maintenance.")
    );
}

function loadDashboard(windowDays) {
    const target = $("#dashboard-analytics");
    if (!target.length) {
        return;
    }
    $.getJSON(target.data("url"), { window: windowDays }, function (data) {
        updateDashboard(data);
    });
}

$(function () {
    const summaryTarget = $("#dashboard-summary-endpoint");
    if (summaryTarget.length) {
        $.getJSON(summaryTarget.data("url"), function (data) {
            $("#summary-total-resources").text(data.total_resources);
            $("#summary-active-resources").text(data.active_resources);
            $("#summary-pending-bookings").text(data.pending_bookings);
        });
    }

    const resourceFilter = $(".js-resource-filter");
    resourceFilter.on("change input", "input, select", function () {
        resourceFilter.trigger("submit");
    });

    resourceFilter.on("submit", function (event) {
        event.preventDefault();
        const apiUrl = $(this).data("api-url");
        const isManager = $(this).data("is-manager") === true || $(this).data("is-manager") === "true";
        $.getJSON(apiUrl, $(this).serialize(), function (data) {
            const cards = data.map((resource) => renderResourceCard(resource, isManager)).join("");
            $("#resource-results").html(cards || '<div class="col-12"><div class="app-panel text-center text-secondary">No resources found.</div></div>');
        });
    });

    const bookingForm = $(".js-booking-form");
    if (bookingForm.length) {
        bookingForm.find("#id_requested_start, #id_requested_end").on("change input", function () {
            updateBookingPreview(bookingForm);
        });
        bookingForm.find("#id_resource").on("change", function () {
            updateBookingPreview(bookingForm);
        });
        updateBookingPreview(bookingForm);
        bookingForm.on("submit", function () {
            enforceBookingWindow(bookingForm.find("#id_requested_start"), false);
            enforceBookingWindow(bookingForm.find("#id_requested_end"), true);
        });
    }

    $("#check-availability").on("click", function () {
        if (!bookingForm.length) {
            return;
        }
        enforceBookingWindow(bookingForm.find("#id_requested_start"), false);
        enforceBookingWindow(bookingForm.find("#id_requested_end"), true);
        updateBookingPreview(bookingForm);
        const payload = {
            resource: bookingForm.find("#id_resource").val(),
            start: bookingForm.find("#id_requested_start").val(),
            end: bookingForm.find("#id_requested_end").val(),
            booking_id: bookingForm.data("booking-id"),
        };

        $.getJSON(bookingForm.data("availability-url"), payload, function (data) {
            $("#availability-result")
                .text(data.message)
                .removeClass("text-success text-danger")
                .addClass(data.available ? "text-success" : "text-danger");
            $("#availability-suggestions").html(renderSuggestions(data));
            if (data.duration_hours > 0) {
                $("#booking-duration").text(`${Number(data.duration_hours).toFixed(1)} hours`);
                $("#booking-cost").text(formatCurrency(data.estimated_cost || 0));
            }
        });
    });

    $(document).on("click", ".suggested-slot", function () {
        if (!bookingForm.length) {
            return;
        }
        bookingForm.find("#id_requested_start").val($(this).data("start"));
        bookingForm.find("#id_requested_end").val($(this).data("end"));
        updateBookingPreview(bookingForm);
        $("#availability-result")
            .text("Suggested slot applied. Click Check Availability to confirm and submit.")
            .removeClass("text-danger text-success")
            .addClass("text-success");
    });

    $(".js-booking-action").on("click", function () {
        const button = $(this);
        $.ajax({
            url: button.data("url"),
            method: "POST",
            data: { status: button.data("status") },
            headers: { "X-CSRFToken": getCsrfToken() },
            success: function (data) {
                alert(data.message);
                window.location.reload();
            },
            error: function (xhr) {
                const message = xhr.responseJSON?.message || "Unable to process the request.";
                alert(message);
            },
        });
    });

    const dashboardTarget = $("#dashboard-analytics");
    if (dashboardTarget.length) {
        const defaultWindow = Number(dashboardTarget.data("default-window")) || 30;
        loadDashboard(defaultWindow);
        $(".js-dashboard-window").on("click", function () {
            $(".js-dashboard-window").removeClass("active");
            $(this).addClass("active");
            loadDashboard(Number($(this).data("window")));
        });
        setInterval(function () {
            const activeButton = $(".js-dashboard-window.active");
            loadDashboard(Number(activeButton.data("window")) || defaultWindow);
        }, 60000);
    }
});
