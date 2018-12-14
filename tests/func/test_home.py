def test_home_redirect_to_login(base_url, selenium):
    selenium.get(base_url + '/home')
    assert 'Login' in selenium.title

    # Fill login form and submit
    field = selenium.find_element_by_css_selector("input#inputUsername")
    field.send_keys('admin')
    field = selenium.find_element_by_css_selector("input#inputPassword")
    field.send_keys('admin')
    selenium.find_element_by_css_selector("form").submit()


def test_home(selenium):
    # Wait for #instances to appear
    selenium.find_element_by_css_selector("#instances")
    assert 'Home' in selenium.title
