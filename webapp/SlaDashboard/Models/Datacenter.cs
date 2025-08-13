
namespace SlaDashboard.Models;
public class Datacenter {
  public int Id { get; set; }
  public string DcId { get; set; } = "";
  public string Region { get; set; } = "";
  public int AreaSqft { get; set; }
  public string Manager { get; set; } = "";
}
