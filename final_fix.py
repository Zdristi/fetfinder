# Финальный скрипт для исправления ошибок
with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\templates\\edit_profile.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправим синтаксис шаблона Jinja2 и удалим дублирование
# Найдем и заменим проблемный блок вручную

correct_block = '''        <!-- Extended Profile Fields -->
        <div class="extended-profile-section">
            <h3 class="section-title-text">
                <i class="fas fa-user-circle"></i> {{ get_text('extended_profile') or 'Extended Profile' }}
            </h3>
            
            <div class="profile-fields-grid">
                <div class="form-group">
                    <label for="about_me_video" class="form-label">{{ get_text('about_me_video') }}</label>
                    <input type="url" id="about_me_video" name="about_me_video" class="form-control" 
                           value="{{ user.about_me_video or '' }}" 
                           placeholder="{{ get_text('about_me_video') }} (YouTube, Vimeo, etc.)">
                </div>
                
                <div class="form-group">
                    <label for="relationship_goals" class="form-label">{{ get_text('relationship_goals') }}</label>
                    <select id="relationship_goals" name="relationship_goals" class="form-control">
                        <option value="">{{ get_text('select_option') or 'Select option' }}</option>
                        <option value="Long-term relationship" {% if user.relationship_goals == 'Long-term relationship' %}selected{% endif %}>{{ get_text('long_term_relationship') or 'Long-term relationship' }}</option>
                        <option value="Short-term fun" {% if user.relationship_goals == 'Short-term fun' %}selected{% endif %}>{{ get_text('short_term_fun') or 'Short-term fun' }}</option>
                        <option value="Marriage" {% if user.relationship_goals == 'Marriage' %}selected{% endif %}>{{ get_text('marriage') or 'Marriage' }}</option>
                        <option value="Friends" {% if user.relationship_goals == 'Friends' %}selected{% endif %}>{{ get_text('friends') or 'Friends' }}</option>
                        <option value="Open relationship" {% if user.relationship_goals == 'Open relationship' %}selected{% endif %}>{{ get_text('open_relationship') or 'Open relationship' }}</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="lifestyle" class="form-label">{{ get_text('lifestyle') }}</label>
                    <select id="lifestyle" name="lifestyle" class="form-control">
                        <option value="">{{ get_text('select_option') or 'Select option' }}</option>
                        <option value="Active" {% if user.lifestyle == 'Active' %}selected{% endif %}>{{ get_text('active') or 'Active' }}</option>
                        <option value="Sedentary" {% if user.lifestyle == 'Sedentary' %}selected{% endif %}>{{ get_text('sedentary') or 'Sedentary' }}</option>
                        <option value="Moderate" {% if user.lifestyle == 'Moderate' %}selected{% endif %}>{{ get_text('moderate') or 'Moderate' }}</option>
                        <option value="Very Active" {% if user.lifestyle == 'Very Active' %}selected{% endif %}>{{ get_text('very_active') or 'Very Active' }}</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="diet" class="form-label">{{ get_text('diet') }}</label>
                    <select id="diet" name="diet" class="form-control">
                        <option value="">{{ get_text('select_option') or 'Select option' }}</option>
                        <option value="Vegetarian" {% if user.diet == 'Vegetarian' %}selected{% endif %}>{{ get_text('vegetarian') or 'Vegetarian' }}</option>
                        <option value="Vegan" {% if user.diet == 'Vegan' %}selected{% endif %}>{{ get_text('vegan') or 'Vegan' }}</option>
                        <option value="Omnivore" {% if user.diet == 'Omnivore' %}selected{% endif %}>{{ get_text('omnivore') or 'Omnivore' }}</option>
                        <option value="Pescatarian" {% if user.diet == 'Pescatarian' %}selected{% endif %}>{{ get_text('pescatarian') or 'Pescatarian' }}</option>
                        <option value="Keto" {% if user.diet == 'Keto' %}selected{% endif %}>{{ get_text('keto') or 'Keto' }}</option>
                        <option value="Paleo" {% if user.diet == 'Paleo' %}selected{% endif %}>{{ get_text('paleo') or 'Paleo' }}</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="smoking" class="form-label">{{ get_text('smoking') }}</label>
                    <select id="smoking" name="smoking" class="form-control">
                        <option value="">{{ get_text('select_option') or 'Select option' }}</option>
                        <option value="Never" {% if user.smoking == 'Never' %}selected{% endif %}>{{ get_text('never') or 'Never' }}</option>
                        <option value="Occasionally" {% if user.smoking == 'Occasionally' %}selected{% endif %}>{{ get_text('occasionally') or 'Occasionally' }}</option>
                        <option value="Socially" {% if user.smoking == 'Socially' %}selected{% endif %}>{{ get_text('socially') or 'Socially' }}</option>
                        <option value="Regularly" {% if user.smoking == 'Regularly' %}selected{% endif %}>{{ get_text('regularly') or 'Regularly' }}</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="drinking" class="form-label">{{ get_text('drinking') }}</label>
                    <select id="drinking" name="drinking" class="form-control">
                        <option value="">{{ get_text('select_option') or 'Select option' }}</option>
                        <option value="Never" {% if user.drinking == 'Never' %}selected{% endif %}>{{ get_text('never') or 'Never' }}</option>
                        <option value="Occasionally" {% if user.drinking == 'Occasionally' %}selected{% endif %}>{{ get_text('occasionally') or 'Occasionally' }}</option>
                        <option value="Socially" {% if user.drinking == 'Socially' %}selected{% endif %}{{ get_text('socially') or 'Socially' }}</option>
                        <option value="Regularly" {% if user.drinking == 'Regularly' %}selected{% endif %}{{ get_text('regularly') or 'Regularly' }}</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="occupation" class="form-label">{{ get_text('occupation') }}</label>
                    <input type="text" id="occupation" name="occupation" class="form-control" 
                           value="{{ user.occupation or '' }}" 
                           placeholder="{{ get_text('occupation') }}">
                </div>
                
                <div class="form-group">
                    <label for="education" class="form-label">{{ get_text('education') }}</label>
                    <input type="text" id="education" name="education" class="form-control" 
                           value="{{ user.education or '' }}" 
                           placeholder="{{ get_text('education') }}">
                </div>
                
                <div class="form-group">
                    <label for="children" class="form-label">{{ get_text('children') }}</label>
                    <select id="children" name="children" class="form-control">
                        <option value="">{{ get_text('select_option') or 'Select option' }}</option>
                        <option value="None" {% if user.children == 'None' %}selected{% endif %}>{{ get_text('none') or 'None' }}</option>
                        <option value="Yes" {% if user.children == 'Yes' %}selected{% endif %}>{{ get_text('yes') or 'Yes' }}</option>
                        <option value="Want someday" {% if user.children == 'Want someday' %}selected{% endif %}>{{ get_text('want_someday') or 'Want someday' }}</option>
                        <option value="Don't want" {% if user.children == "Don't want" %}selected{% endif %}{{ get_text('dont_want') }}</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="pets" class="form-label">{{ get_text('pets') }}</label>
                    <input type="text" id="pets" name="pets" class="form-control" 
                           value="{{ user.pets or '' }}" 
                           placeholder="{{ get_text('pets') }} ({{ get_text('comma_separated') or 'comma separated' }})">
                </div>
            </div>
        </div>'''

# Найдем позицию начала и конца старого блока
start_pos = content.find('<!-- Extended Profile Fields -->')
if start_pos != -1:
    # Найдем конец блока (до следующего комментария или определенного признака)
    end_pos = content.find('<!-- Additional Photos Section -->', start_pos)
    
    if end_pos != -1:
        # Заменим весь блок
        new_content = content[:start_pos] + correct_block + content[end_pos:]
        
        with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\templates\\edit_profile.html', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("Блок Extended Profile успешно исправлен!")
    else:
        print("Не найден конец блока")
else:
    print("Не найдено начало блока")