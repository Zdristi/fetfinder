#!/usr/bin/env python
# Script to replace the broken swipe route with correct one

with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all broken versions of swipe route
lines = content.split('\n')

# Find and remove all swipe route definitions
new_lines = []
skip_next = False
found_swipe_route = False

for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
        
    # Check if this is the start of the broken swipe route
    if '@app.route(\'/swipe\')' in line:
        found_swipe_route = True
        # Skip this line and all subsequent lines until we reach the next route
        continue
    elif found_swipe_route and '@app.route(' in line:
        # We've reached the next route, stop skipping
        found_swipe_route = False
        new_lines.append(line)
    elif found_swipe_route:
        # Skip this line as it's part of the broken swipe route
        continue
    else:
        new_lines.append(line)

# Insert the correct swipe route before the users route
correct_route = '''@app.route('/swipe')
@login_required
def swipe():
    return render_template('swipe_fresh.html')'''

# Insert the correct route before the users route
final_lines = []
inserted = False
for line in new_lines:
    if '@app.route(\'/users\')' in line and not inserted:
        final_lines.append(correct_route)
        inserted = True
    final_lines.append(line)

# Write back to file
with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\app_fixed_final.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(final_lines))