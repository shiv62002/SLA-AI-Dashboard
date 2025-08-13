using Microsoft.EntityFrameworkCore;
using SlaDashboard.Data;

var builder = WebApplication.CreateBuilder(args);

// SQLite connection
builder.Services.AddDbContext<AppDb>(opt =>
  opt.UseSqlite(builder.Configuration.GetConnectionString("Default") ?? "Data Source=sla.db"));

builder.Services.AddRazorPages();
var aiBase = Environment.GetEnvironmentVariable("AI_BASE") ?? "http://localhost:8001";
builder.Services.AddHttpClient("ai", c => c.BaseAddress = new Uri(aiBase));

var app = builder.Build();

app.MapGet("/healthz", () => Results.Ok(new { ok = true }));


// Seed on startup from ../../data relative to this project folder
using (var scope = app.Services.CreateScope())
{
  var db = scope.ServiceProvider.GetRequiredService<AppDb>();
  var dataDir = Path.Combine(app.Environment.ContentRootPath, "../../data");
  Seed.Ensure(db, dataDir);
}

// Minimal APIs for KPIs and tickets
app.MapGet("/api/kpi/summary", async (AppDb db) =>
{
    var now = DateTime.UtcNow;
    var in7  = now.AddDays(7);
    var in21 = now.AddDays(21);

    var open    = await db.Tickets.CountAsync(t => t.Status == "Open");
    var dueIn7  = await db.Tickets.CountAsync(t => t.Status == "Open" && t.DueDate >= now && t.DueDate <= in7);
    var dueIn21 = await db.Tickets.CountAsync(t => t.Status == "Open" && t.DueDate >= now && t.DueDate <= in21);
    var overdue = await db.Tickets.CountAsync(t => t.Status == "Open" && t.DueDate < now);

    return Results.Ok(new { open, dueIn21, dueIn7, overdue });
});

app.MapGet("/api/tickets", async (AppDb db, string? status, string? dc, string? category) =>
{
    var q = db.Tickets.AsQueryable();
    if (!string.IsNullOrWhiteSpace(status))   q = q.Where(t => t.Status == status);
    if (!string.IsNullOrWhiteSpace(dc))       q = q.Where(t => t.DcId == dc);
    if (!string.IsNullOrWhiteSpace(category)) q = q.Where(t => t.DocCategory == category);

    var nowDate = DateTime.UtcNow.Date;

    // Fetch from DB first, then compute DaysToDue in memory to avoid translation issues
    var items = await q
      .Select(t => new {
        t.TicketId, t.DcId, t.DocCategory, t.Owner, t.Status, t.Priority,
        t.CreatedAt, t.DueDate
      })
      .ToListAsync();

    var list = items.Select(t => new {
      t.TicketId, t.DcId, t.DocCategory, t.Owner, t.Status, t.Priority,
      t.CreatedAt, t.DueDate,
      DaysToDue = (int)(t.DueDate.Date - nowDate).TotalDays
    });

    return Results.Ok(list);
});

// Endpoint tailored for Power Automate reminders
app.MapGet("/api/reminders", async (AppDb db) =>
{
  var today = DateTime.UtcNow.Date;

  var items = await db.Tickets
    .Where(t => t.Status == "Open")
    .Select(t => new
    {
      t.TicketId,
      t.DcId,
      t.DocCategory,
      t.Owner,
      t.Priority,
      t.DueDate
    })
    .ToListAsync();

  var shaped = items.Select(t => new
  {
    t.TicketId,
    t.DcId,
    t.DocCategory,
    t.Owner,
    t.Priority,
    t.DueDate,
    DaysToDue = (int)(t.DueDate.Date - today).TotalDays
  });

  return Results.Ok(shaped);
});

app.MapGet("/api/ai/summary", async (IHttpClientFactory http) =>
{
  var client = http.CreateClient("ai");
  using var res = await client.GetAsync("/summarize");
  res.EnsureSuccessStatusCode();
  var json = await res.Content.ReadAsStringAsync();
  return Results.Content(json, "application/json");
});

// Heatmap aggregation by DC (open tickets only)
app.MapGet("/api/tickets/heatmap", async (AppDb db) =>
{
    var today = DateTime.UtcNow.Date;

    var items = await db.Tickets
        .Where(t => t.Status == "Open")
        .Select(t => new
        {
            t.DcId,
            Days = (int)(t.DueDate.Date - today).TotalDays
        })
        .ToListAsync();

    var groups = items
        .GroupBy(x => x.DcId)
        .Select(g => new
        {
            dcId = g.Key,
            overdue = g.Count(x => x.Days < 0),
            due7    = g.Count(x => x.Days >= 0 && x.Days <= 7),
            due21   = g.Count(x => x.Days >= 8 && x.Days <= 21),
            ok      = g.Count(x => x.Days > 21)
        })
        .OrderBy(x => x.dcId);

    return Results.Ok(groups);
});


app.MapRazorPages();

if (!app.Environment.IsDevelopment()) { app.UseExceptionHandler("/Error"); app.UseHsts(); }
app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseRouting();
app.UseAuthorization();

app.Run();
