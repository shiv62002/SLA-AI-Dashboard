using Microsoft.EntityFrameworkCore;
using SlaDashboard.Models;

namespace SlaDashboard.Data;
public class AppDb : DbContext {
  public AppDb(DbContextOptions<AppDb> opts) : base(opts) {}
  public DbSet<Ticket> Tickets => Set<Ticket>();
  public DbSet<Datacenter> Datacenters => Set<Datacenter>();
}
