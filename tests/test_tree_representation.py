import bs4

from betterhtmlchunking.tree_representation import get_pos_xpath_from_bs4_elem


def test_get_pos_xpath_from_bs4_elem_counts_siblings():
    html = "<html><body><div></div><div></div></body></html>"
    soup = bs4.BeautifulSoup(html, "html.parser")
    divs = soup.find_all("div")
    assert get_pos_xpath_from_bs4_elem(divs[0]) == "/html/body/div[1]"
    assert get_pos_xpath_from_bs4_elem(divs[1]) == "/html/body/div[2]"
