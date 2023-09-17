import sys
import requests
import csv
import json
from pprint import pprint

from bs4 import BeautifulSoup

#  python3 scraper.py "https://volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7103" "vysledky_prostejov.html"

header = ["codes", "location", "registered", "envelopes", "valid"]


def scraper():
    # if len(sys.argv) != 3:
    #     print("Nebyly zadány všechny potřebné parametry.\nUkončuji program.")
    #     sys.exit(1)
    #
    # web_page = sys.argv[1]
    # name_file = sys.argv[2]
    #
    # print(f"STAHUJI DATA Z VYBRANÉHO CÍLE: {sys.argv[1]}")
    # req = requests.get(web_page)

    localni_pozadavek = requests.get("https://volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7103")
    if localni_pozadavek.status_code == 200:
        content = localni_pozadavek.content
        soup = BeautifulSoup(content, "html.parser")

        # print(f"UKLÁDÁM DATA DO SOUBORU: {name_file}")
        # with open(name_file, mode="w", encoding="UTF-8") as file:
        #     file.write(soup.prettify())
        return soup


def location_scraper_by_code(soup):
    """Stahování dat z jednotlivých obcí"""
    # extrakce požadovaných dat
    numbers = soup.find_all("td", class_="cislo")
    names = soup.find_all("td", class_="overflow_name")

    kody = [int(number.getText(strip=True)) for number in numbers]
    locations = [name.get_text(strip=True) for name in names]
    links = [f"https://volby.cz/pls/ps2017nss/ps311?xjazyk=CZ&xkraj=12&xobec={kod}&xvyber=7103"
             for kod in kody]
    cykl = 0

    valid = []
    registered = []
    envelopes = []
    volebni_strany = {}

    for link in links[0:1]:
        cykl += 1

        location_resp_by_code = requests.get(link)
        if location_resp_by_code.status_code == 200:
            location_soup = BeautifulSoup(location_resp_by_code.content, "html.parser")

            nazvy = location_soup.find_all("td", class_="overflow_name")
            registered.append(location_soup.select_one("td:nth-child(4)").get_text(strip=True))
            envelopes.append(location_soup.select_one("td:nth-child(7)").get_text(strip=True))
            valid.append(location_soup.select_one("td:nth-child(8)").get_text(strip=True))
            hlasy = location_soup.select("td:nth-child(3)")

            hlasy_stran = [hlas.getText(strip=True) for hlas in hlasy[1:-1]]
            strany = [nazev.getText(strip=True) for nazev in nazvy]  # 25 stran

        print(f"Location scraper {cykl}/{len(links)}...OK")

    for i, name in enumerate(strany):
        volebni_strany[name] = hlasy_stran[i]

    return kody, locations, registered, envelopes, valid, volebni_strany, strany, hlasy_stran


def pridej_data():
    for key, value in volebni_strany.items():
        data_dict[key] = value
    return data_dict


def database_builder(codes, location, registered, envelopes, valid, volebni_strany, data_dict):
    ziped_data = zip(codes, location, registered, envelopes, valid, volebni_strany)

    for data in ziped_data:
        kod, lokalita, reg, env, val, strana = data
        data_dict[lokalita] = {
            'Kod Obce': kod,
            'Location': lokalita,
            'Registered': reg,
            'Envelopes': env,
            'Valid Votes': val

        }
    pridej_data()
    return data_dict


def json_out():
    json_soubor = open("muj_json", mode="w")
    json.dump(data_dict, json_soubor)
    json.dump(volebni_strany, json_soubor)
    json_soubor.close()
    print(f"JSON created...")


def generate_output(header, data_dict):
    """Zápis dat do souboru"""
    with open("vystup_vysledku_voleb_csv", mode="w") as output:
        writer = csv.writer(output)
        writer.writerow(header)
        writer.writerow(data_dict.keys())

        print("Zápis byl úspěšně proveden.")


def scraper_end():
    print("HOTOVO!\nUkončuji Election-scraper.")


if __name__ == "__main__":
    data_dict = {}
    soup = scraper()
    codes, location, registered, envelopes, valid, volebni_strany, strany, hlasy_stran = location_scraper_by_code(soup)
    database_builder(codes, location, registered, envelopes, valid, volebni_strany, data_dict)
    json_out()
    generate_output(header, data_dict)

    pprint(data_dict)
