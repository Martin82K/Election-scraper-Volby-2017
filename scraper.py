import sys
import requests
import csv

from bs4 import BeautifulSoup


def scraper():
    """
    Ukázka: #  python3 scraper.py "https://volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7103" "vysledky_projekt3.csv"
    :return:
    """
    if len(sys.argv) != 3:
        print("Nebyly zadány všechny potřebné parametry.\nUkončuji program.")
        print("Prosím přečtěte si přiloženou dokumentaci a akci opakujte.")
        sys.exit(1)

    web_page = sys.argv[1]
    name_file = sys.argv[2]

    print(f"STAHUJI DATA Z VYBRANÉHO CÍLE: {sys.argv[1]}")
    # req = requests.get(web_page)

    soup = bs_soup(web_page)
    city_code_numbers_new = city_code_numbers(soup)
    city_names_new = city_names(soup)
    scraped_city_data, parties_all = city_scraper(city_code_numbers_new, city_names_new)
    header = header_maker(parties_all)
    output_to_csv(scraped_city_data, header, name_file)


def bs_soup(web_page):
    pozadavek = requests.get(web_page)

    if pozadavek.status_code == 200:
        soup = BeautifulSoup(pozadavek.content, "html.parser")
        return soup


def city_code_numbers(soup):
    city_numbers = soup.find_all("td", class_="cislo")
    city_code_numbers_new = [int(number.getText(strip=True)) for number in city_numbers]
    return city_code_numbers_new


def city_names(soup):
    names = soup.find_all("td", class_="overflow_name")
    city_names_new = [name.get_text(strip=True) for name in names]
    return city_names_new


def city_links(city_code_numbers_new):
    city_part_link = [f"https://volby.cz/pls/ps2017nss/ps311?xjazyk=CZ&xkraj=12&xobec={number}&xvyber=7103"
                      for number in city_code_numbers_new]
    return city_part_link


def city_scraper(city_code_numbers_new, city_names_new):
    print("Stahuji data z jednotlivých obcí...")
    scraped_city_data = []

    for index, number in enumerate(city_code_numbers_new):
        city_part_scraper = requests.get(
            f"https://volby.cz/pls/ps2017nss/ps311?xjazyk=CZ&xkraj=12&xobec={number}&xvyber=7103")

        city_part_soup = BeautifulSoup(city_part_scraper.content, "html.parser")

        city_name = city_names_new[index]

        registered = (city_part_soup.select_one("td:nth-child(4)").get_text(strip=True))
        envelopes = (city_part_soup.select_one("td:nth-child(7)").get_text(strip=True))
        valid = (city_part_soup.select_one("td:nth-child(8)").get_text(strip=True))

        voices_data = city_part_soup.select("td:nth-child(3)")
        voices_parties = [voice.getText(strip=True) for voice in voices_data[1:-1]]

        parties_data = city_part_soup.find_all("td", class_="overflow_name")
        parties_all = ([party.getText(strip=True) for party in parties_data])

        elect_parties_with_voices = dict()

        for i, name in enumerate(parties_all):
            elect_parties_with_voices[name] = voices_parties[i]

        data_city = {
            'codes': number,
            'location': city_name,
            'registered': registered,
            'envelopes': envelopes,
            'valid': valid
        }
        for key, value in elect_parties_with_voices.items():
            data_city[key] = value

        scraped_city_data.append(data_city)

    return scraped_city_data, parties_all


def header_maker(parties_all):
    header = ["codes", "location", "registered", "envelopes", "valid"]
    for party in parties_all:
        header.append(party)
    return header


def output_to_csv(scraped_city_data, header, name_file):
    print("Zapisuji do souboru:", name_file)
    with open(name_file, mode="w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=header, dialect="excel")
        writer.writeheader()
        for city in scraped_city_data:
            if city == 0:
                continue
            else:
                writer.writerow(city)
    print("HOTOVO, ukončuji election scraper.")


if __name__ == "__main__":
    scraper()
