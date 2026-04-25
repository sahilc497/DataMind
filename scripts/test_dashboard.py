import requests
import json

r = requests.get('http://localhost:8000/dashboard')
print(f"Status: {r.status_code}")

if r.status_code == 200:
    d = r.json()
    print(f"Total Machines: {d.get('total_machines', 0)}")
    print(f"Critical: {d.get('critical_count', 0)}, Warning: {d.get('warning_count', 0)}, Healthy: {d.get('healthy_count', 0)}")
    print()
    for m in d.get('machines', []):
        h = m.get('health', {})
        p = m.get('prediction', {})
        mt = m.get('metrics', {})
        print(f"  {m['name']} ({m['type']})")
        print(f"    Status: {h.get('status', '?')} | Failure Risk: {p.get('failure_probability', 0)*100:.0f}% | Trend: {p.get('trend', '?')}")
        print(f"    Temp: {mt.get('avg_temperature', 0):.1f}°C | Vib: {mt.get('avg_vibration', 0):.2f} mm/s | RPM: {mt.get('avg_rpm', 0):.0f}")
        if h.get('diagnoses'):
            for diag in h['diagnoses'][:2]:
                print(f"    ⚠️  {diag['issue']} ({diag['severity']}, {diag['confidence']}% conf)")
        print()
    
    print("Fleet Insights:")
    for ins in d.get('fleet_insights', []):
        print(f"  {ins['text']}")
else:
    print(f"Error: {r.text}")
