"""Deterministic, idempotent sample data (India) that shows the matching engine at work.

Deliberate cases (see comments): synonyms with no shared words, near misses that the
hard filters must exclude (quantity, budget, lead time, distance, box vs piece),
same-category distractors, competing suppliers, and one supplier fitting several needs.
Prices are in rupees (INR). Coordinates are included so the demo does not depend on a geocoder.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Offering, Requirement

CITIES = {
    "Mumbai": (19.0760, 72.8777),
    "Thane": (19.2183, 72.9781),
    "Pune": (18.5204, 73.8567),
    "Delhi": (28.6139, 77.2090),
    "Gurugram": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
    "Jaipur": (26.9124, 75.7873),
    "Ludhiana": (30.9010, 75.8573),
    "Ahmedabad": (23.0225, 72.5714),
    "Vadodara": (22.3072, 73.1812),
    "Surat": (21.1702, 72.8311),
    "Rajkot": (22.3039, 70.8022),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Coimbatore": (11.0168, 76.9558),
    "Hyderabad": (17.3850, 78.4867),
    "Kolkata": (22.5726, 88.3639),
    "Nagpur": (21.1458, 79.0882),
}

METALS = "Raw Materials & Metals"
ELEC = "Electronics & Electrical"
PACK = "Packaging"
FOOD = "Food & Agriculture"
BUILD = "Construction Materials"
OFFICE = "Office & Consumables"

# One row per line reads better than the formatter's layout for a data table.
# fmt: off
# client, email, product, category, quantity, unit, budget (INR, total), city, needed_within_days, notes
REQUIREMENTS = [
    ("Shree Ganesh Fabricators", "buyer@shreeganesh.example.com", "MS pipes, 2 inch diameter", METALS, 2000, "kg", 150000, "Pune", 21, "For process water lines"),
    ("Coastline Shipyards", "procurement@coastline.example.com", "Stainless steel sheet 304, 3 mm", METALS, 1, "tonne", 400000, "Chennai", 30, None),
    ("Apex Die Casting", "materials@apexdie.example.com", "Aluminium ingots for die casting", METALS, 5, "tonne", 1200000, "Pune", 30, None),
    ("Mumbai Railings", "orders@mumbairailings.example.com", "Steel tubes for handrails", METALS, 800, "kg", 60000, "Mumbai", 14, "Round section, galvanised preferred"),
    ("Precision Fittings", "buy@precisionfit.example.com", "Brass rods 12 mm", METALS, 300, "kg", 210000, "Rajkot", 20, None),
    ("Roshni Retail", "sourcing@roshniretail.example.com", "LED bulbs 9W warm white", ELEC, 5000, "piece", 400000, "Delhi", 30, "E27 or B22 base"),
    ("Volt Contractors", "stores@voltcontractors.example.com", "Copper electrical cable 2.5 sq mm", ELEC, 2000, "metre", 90000, "Mumbai", 14, "Domestic rewiring jobs"),
    ("SuryaNest Solar", "supply@suryanest.example.com", "Solar panels 400W monocrystalline", ELEC, 50, "piece", 700000, "Jaipur", 45, None),
    ("FactoryTech", "maintenance@factorytech.example.com", "Industrial circuit breakers MCB 32A", ELEC, 400, "piece", 160000, "Pune", 20, None),
    ("Nagpur Municipal Works", "streets@nmw.example.com", "LED street light fixtures 100W", ELEC, 120, "piece", 1200000, "Nagpur", 60, "Outdoor, IP65 or better"),
    ("FreshBox Foods", "packaging@freshbox.example.com", "Corrugated cardboard boxes for shipping", PACK, 10000, "piece", 350000, "Mumbai", 14, None),
    ("GreenLeaf Cosmetics", "ops@greenleaf.example.com", "Biodegradable paper mailer bags", PACK, 5000, "piece", 100000, "Bengaluru", 21, None),
    ("Hops & Barley Brewing", "brewery@hopsbarley.example.com", "Glass bottles 330ml amber", PACK, 20000, "piece", 400000, "Bengaluru", 30, "For craft beer"),
    ("Pune Logistics Park", "depot@punelogistics.example.com", "Wooden pallets EUR standard", PACK, 300, "piece", 360000, "Pune", 10, None),
    ("Chatpata Snacks", "buying@chatpata.example.com", "Food grade plastic containers with lids 500ml", PACK, 10000, "piece", 200000, "Ahmedabad", 20, None),
    ("Spice Route Restaurants", "kitchen@spiceroute.example.com", "Organic basmati rice", FOOD, 2, "tonne", 300000, "Delhi", 30, None),
    ("Bangalore Bakers", "flour@blrbakers.example.com", "Wheat flour for bread baking", FOOD, 5000, "kg", 200000, "Bengaluru", 7, None),
    ("Trattoria Mumbai", "chef@trattoriamumbai.example.com", "Extra virgin olive oil", FOOD, 1000, "litre", 900000, "Mumbai", 30, None),
    ("Bean There Coffee", "roastery@beanthere.example.com", "Arabica coffee beans, green, unroasted", FOOD, 3, "tonne", 1500000, "Bengaluru", 45, None),
    ("Juice Junction", "orders@juicejunction.example.com", "Fresh oranges for juicing", FOOD, 2000, "kg", 140000, "Nagpur", 5, None),
    ("BuildRight Infra", "site@buildright.example.com", "Portland cement OPC 53 grade", BUILD, 20, "tonne", 180000, "Hyderabad", 14, None),
    ("Metro Homes", "procure@metrohomes.example.com", "TMT steel reinforcement bars 12mm", BUILD, 10, "tonne", 650000, "Mumbai", 21, None),
    ("Metro Homes", "procure@metrohomes.example.com", "Ceramic floor tiles 600x600", BUILD, 2000, "piece", 900000, "Mumbai", 45, None),
    ("GreenBuild Chennai", "buyer@greenbuild.example.com", "Mineral wool insulation rolls", BUILD, 400, "piece", 800000, "Chennai", 20, "Roof insulation"),
    ("Coastal Roads", "materials@coastalroads.example.com", "Washed river sand for concrete", BUILD, 50, "tonne", 150000, "Chennai", 10, None),
    ("LedgerCo", "office@ledgerco.example.com", "A4 printer paper 80gsm", OFFICE, 500, "box", 800000, "Delhi", 10, None),
    ("Startup Hub", "admin@startuphub.example.com", "Ergonomic office chairs", OFFICE, 40, "piece", 400000, "Bengaluru", 21, None),
    ("Jaipur Schools Trust", "supplies@jst.example.com", "Blue ballpoint pens", OFFICE, 5000, "piece", 50000, "Jaipur", 30, None),
    ("LedgerCo", "office@ledgerco.example.com", "Black toner cartridges for HP LaserJet", OFFICE, 60, "piece", 240000, "Delhi", 7, None),
    ("Startup Hub", "admin@startuphub.example.com", "Standing desks, height adjustable", OFFICE, 20, "piece", 700000, "Bengaluru", 30, None),
]

# supplier, email, product, category, available_qty, unit, unit_price (INR), pricing_notes,
# city, lead_time_days, delivery_scope, notes
OFFERINGS = [
    # "MS pipes": synonym (no shared words), a competitor, and three near misses
    ("Bharat Tubes", "sales@bharattubes.example.com", "Mild steel tubes, 50 mm OD", METALS, 5000, "kg", 68, "5% off above 3 tonnes", "Mumbai", 7, "regional", "Round tube, galvanised option"),
    ("Deccan Pipe Works", "sales@deccanpipe.example.com", "ERW mild steel pipe 2 inch", METALS, 1.5, "tonne", 70000, None, "Nagpur", 10, "national", None),
    ("Sai Metals", "trade@saimetals.example.com", "MS pipes 2 inch", METALS, 3000, "kg", 120, None, "Mumbai", 5, "national", None),  # far over budget
    ("QuickPipe Traders", "hello@quickpipe.example.com", "Mild steel pipes 2 inch", METALS, 300, "kg", 66, None, "Pune", 2, "local", None),  # too little stock
    ("Konkan Steel", "orders@konkansteel.example.com", "MS pipe 2 inch, black", METALS, 10000, "kg", 60, None, "Mumbai", 60, "regional", None),  # too slow
    ("Sheetkraft Industries", "sales@sheetkraft.example.com", "Cold rolled steel sheets 2 mm", METALS, 8000, "kg", 62, None, "Pune", 5, "local", None),  # distractor
    ("Hindustan Alloys", "export@hindalloys.example.com", "Aluminium ingots 99.7% purity", METALS, 20, "tonne", 230000, None, "Kolkata", 21, "national", None),
    ("Sagar Stainless", "sales@sagarstainless.example.com", "SS 304 plates 3 mm", METALS, 2, "tonne", 320000, None, "Ahmedabad", 14, "national", None),
    ("Jamnagar Brass Works", "counter@jamnagarbrass.example.com", "Brass round bar 12 mm CZ121", METALS, 1000, "kg", 650, None, "Rajkot", 3, "local", None),
    # LED bulbs: competitors, a distractor, and a box-vs-piece near miss
    ("Chennai Lumen", "sales@chennailumen.example.com", "9 watt LED lamps, 2700K, E27", ELEC, 20000, "piece", 70, "MOQ 2000", "Chennai", 25, "national", None),
    ("Dilli Lighting", "trade@dillilighting.example.com", "LED light bulbs 9W B22 warm white", ELEC, 3000, "piece", 78, None, "Delhi", 5, "national", None),
    ("StripGlow", "sales@stripglow.example.com", "LED strip lights RGB 5m", ELEC, 2000, "piece", 75, None, "Delhi", 3, "national", None),  # distractor
    ("BoxedBulbs", "sales@boxedbulbs.example.com", "LED bulbs 9W warm white, box of 10", ELEC, 1000, "box", 700, None, "Noida", 3, "national", None),  # box != piece
    ("Thane Cables", "sales@thanecables.example.com", "2.5mm twin and earth copper wire", ELEC, 10000, "metre", 40, None, "Thane", 4, "regional", None),
    ("Kolkata Wires", "export@kolkatawires.example.com", "PVC insulated copper wire 2.5 sqmm", ELEC, 50000, "metre", 30, None, "Kolkata", 35, "national", None),  # too slow
    ("SunHarvest Energy", "b2b@sunharvest.example.com", "400 watt mono PERC solar modules", ELEC, 500, "piece", 12000, None, "Ahmedabad", 20, "national", None),
    ("BudgetSolar", "sales@budgetsolar.example.com", "Polycrystalline solar panel 330W", ELEC, 200, "piece", 9500, None, "Delhi", 10, "national", None),
    ("Circuit Supply Co", "trade@circuitsupply.example.com", "32 amp miniature circuit breaker, C curve", ELEC, 2000, "piece", 350, None, "Mumbai", 7, "national", None),
    ("StreetLux", "sales@streetlux.example.com", "100W LED street lamp luminaire IP66", ELEC, 500, "piece", 8500, None, "Hyderabad", 40, "national", None),
    # Cardboard boxes: two competitors (one short on stock) and a distractor
    ("Bhiwandi Packaging", "sales@bhiwandipack.example.com", "Double wall carton boxes 400x300x300", PACK, 50000, "piece", 30, None, "Thane", 5, "local", None),
    ("Vapi Cartons", "orders@vapicartons.example.com", "Brown shipping cartons, 5-ply corrugated", PACK, 8000, "piece", 27, None, "Surat", 7, "regional", None),
    ("WrapIt", "sales@wrapit.example.com", "Stretch film pallet wrap rolls", PACK, 5000, "piece", 50, None, "Mumbai", 3, "regional", None),  # distractor
    ("EcoMail", "hello@ecomail.example.com", "Compostable kraft paper mailers", PACK, 20000, "piece", 16, None, "Bengaluru", 10, "local", None),
    ("Deccan Glassworks", "sales@deccanglass.example.com", "330 ml amber beer bottles", PACK, 100000, "piece", 17, None, "Hyderabad", 12, "national", None),
    ("Pallet King", "yard@palletking.example.com", "Euro pallets 1200x800 heat treated", PACK, 1000, "piece", 1000, None, "Mumbai", 3, "regional", None),
    ("DabbaPack", "sales@dabbapack.example.com", "500ml PP containers with lids", PACK, 30000, "piece", 15, None, "Vadodara", 6, "regional", None),
    # Rice sold per tonne and per kg (unit conversion)
    ("Punjab Grains", "export@punjabgrains.example.com", "Long grain aromatic basmati rice, certified organic", FOOD, 20, "tonne", 130000, None, "Ludhiana", 28, "national", None),
    ("Azadpur Wholesale", "trade@azadpur.example.com", "Basmati rice premium, organic", FOOD, 1500, "kg", 145, None, "Delhi", 3, "local", None),
    ("Coimbatore Flour Mills", "orders@cbeflour.example.com", "Strong white bread flour (maida), 50 kg sacks", FOOD, 20000, "kg", 34, None, "Coimbatore", 2, "regional", None),
    ("Artisan Mills", "sales@artisanmills.example.com", "Bread flour T65", FOOD, 10000, "kg", 33, None, "Chennai", 20, "regional", None),  # too slow
    ("Olivia Imports", "b2b@oliviaimports.example.com", "Cold pressed extra virgin olive oil in 5L tins", FOOD, 5000, "litre", 780, None, "Delhi", 14, "national", None),
    ("Suraj Oils", "sales@surajoils.example.com", "Refined sunflower oil", FOOD, 8000, "litre", 140, None, "Pune", 5, "regional", None),  # distractor
    ("Coorg Green Bean Traders", "trade@coorggreen.example.com", "Green arabica coffee, washed, 60kg bags", FOOD, 15000, "kg", 450, None, "Coimbatore", 25, "regional", None),
    ("Nagpur Citrus", "orders@nagpurcitrus.example.com", "Nagpur oranges, juicing grade", FOOD, 10000, "kg", 60, None, "Nagpur", 2, "local", None),
    # Construction
    ("Deccan Cement", "sales@deccancement.example.com", "OPC 53 cement, 50 kg bags", BUILD, 200, "tonne", 7800, None, "Hyderabad", 3, "local", None),
    ("SmallBatch Cement", "hello@smallbatch.example.com", "Ordinary Portland cement", BUILD, 4, "tonne", 7500, None, "Hyderabad", 2, "local", None),  # too little stock
    ("Nagpur TMT Bars", "sales@nagpurtmt.example.com", "12 mm TMT rebar, Fe 500D, 12 m lengths", BUILD, 50, "tonne", 58000, None, "Nagpur", 10, "national", None),
    ("Morbi Ceramics", "export@morbiceramics.example.com", "600x600 vitrified porcelain floor tiles", BUILD, 10000, "piece", 380, None, "Rajkot", 35, "national", None),
    ("Coromandel Insulation", "sales@coromandel.example.com", "Glass wool insulation roll 100mm", BUILD, 1000, "piece", 1700, None, "Bengaluru", 7, "regional", None),
    ("Chennai Aggregates", "quarry@chennaiagg.example.com", "Sharp sand, washed, bulk bags", BUILD, 500, "tonne", 2400, None, "Chennai", 2, "local", None),
    # Office: paper sold per box and per ream (box != piece)
    ("PaperPoint", "sales@paperpoint.example.com", "Copy paper A4 80 gsm, 5 reams per box", OFFICE, 2000, "box", 1400, None, "Delhi", 2, "local", None),
    ("ReamSource", "orders@reamsource.example.com", "A4 printer paper 80gsm ream", OFFICE, 5000, "piece", 300, None, "Delhi", 2, "local", None),  # piece != box
    ("SitWell Furniture", "sales@sitwell.example.com", "Mesh task chairs with lumbar support", OFFICE, 200, "piece", 8500, None, "Bengaluru", 10, "regional", None),
    ("PenWorld", "sales@penworld.example.com", "Ballpoint pens blue ink, medium point", OFFICE, 50000, "piece", 6, None, "Kolkata", 20, "national", None),
    ("TonerHouse", "sales@tonerhouse.example.com", "Compatible HP 26A black toner", OFFICE, 300, "piece", 3200, None, "Gurugram", 1, "local", None),
    # One supplier fitting several office needs
    ("SitWell Furniture", "sales@sitwell.example.com", "Electric sit-stand desks", OFFICE, 100, "piece", 28000, None, "Bengaluru", 14, "regional", None),
]
# fmt: on


def _coords(city: str) -> dict:
    lat, lon = CITIES[city]
    return {"location": city, "latitude": lat, "longitude": lon}


def seed(db: Session) -> dict:
    """Insert rows that are not there yet (keyed on email + product). Safe to call twice."""
    have_req = set(db.execute(select(Requirement.contact_email, Requirement.product_requirement)))
    have_off = set(db.execute(select(Offering.contact_email, Offering.product_offered)))
    new_req = [
        Requirement(
            client_name=name,
            contact_email=email,
            product_requirement=product,
            category=cat,
            quantity=qty,
            unit=unit,
            budget=budget,
            needed_within_days=days,
            notes=notes,
            **_coords(city),
        )
        for name, email, product, cat, qty, unit, budget, city, days, notes in REQUIREMENTS
        if (email, product) not in have_req
    ]
    new_off = [
        Offering(
            supplier_name=name,
            contact_email=email,
            product_offered=product,
            category=cat,
            available_quantity=qty,
            unit=unit,
            unit_price=price,
            pricing_notes=pricing,
            lead_time_days=lead,
            delivery_scope=scope,
            notes=notes,
            **_coords(city),
        )
        for name, email, product, cat, qty, unit, price, pricing, city, lead, scope, notes in OFFERINGS
        if (email, product) not in have_off
    ]
    db.add_all(new_req + new_off)
    db.commit()
    return {"requirements_created": len(new_req), "offerings_created": len(new_off)}
