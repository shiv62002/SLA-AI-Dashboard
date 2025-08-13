using CsvHelper;
using CsvHelper.Configuration;
using SlaDashboard.Models;
using System.Globalization;

namespace SlaDashboard.Data;

public static class Seed {
  public static void Ensure(AppDb db, string dataDir) {
    db.Database.EnsureCreated();

    if (!db.Datacenters.Any()) {
      var cfg = new CsvConfiguration(CultureInfo.InvariantCulture){HasHeaderRecord=true, TrimOptions=TrimOptions.Trim};
      using var reader = new StreamReader(Path.Combine(dataDir,"datacenters.csv"));
      using var csv = new CsvReader(reader, cfg);
      foreach (var r in csv.GetRecords<dynamic>()) {
        db.Datacenters.Add(new Datacenter{
          DcId = r.dc_id, Region = r.region,
          AreaSqft = int.Parse(r.area_sqft), Manager = r.manager
        });
      }
    }

    if (!db.Tickets.Any()) {
      var cfg = new CsvConfiguration(CultureInfo.InvariantCulture){HasHeaderRecord=true, TrimOptions=TrimOptions.Trim};
      using var reader = new StreamReader(Path.Combine(dataDir,"tickets.csv"));
      using var csv = new CsvReader(reader, cfg);
      foreach (var r in csv.GetRecords<dynamic>()) {
        db.Tickets.Add(new Ticket{
          TicketId = r.ticket_id,
          DcId = r.dc_id,
          DocCategory = r.doc_category,
          CreatedAt = DateTime.Parse(r.created_at),
          DueDate = DateTime.Parse(r.due_date),
          Owner = r.owner,
          Status = r.status,
          Priority = r.priority
        });
      }
    }

    db.SaveChanges();
  }
}
