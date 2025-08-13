namespace SlaDashboard.Models;
public class Ticket {
  public int Id { get; set; }
  public string TicketId { get; set; } = "";
  public string DcId { get; set; } = "";
  public string DocCategory { get; set; } = "";
  public DateTime CreatedAt { get; set; }
  public DateTime DueDate { get; set; }
  public string Owner { get; set; } = "";
  public string Status { get; set; } = "Open";
  public string Priority { get; set; } = "Medium";
}
