import argparse
import os
import logging
import colorama
from colorama import Fore, Style
from . import client  # Importing client from a module named "client"
from urllib.parse import urlparse, parse_qs, urlencode

yellow_color_code = "\033[93m"
reset_color_code = "\033[0m"

colorama.init(autoreset=True)  # Initialize colorama for colored terminal output

log_format = '%(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)
logging.getLogger('').handlers[0].setFormatter(logging.Formatter(log_format))

HARDCODED_EXTENSIONS = [
    ".jpg", ".jpeg", ".png", ".gif", ".pdf", ".svg", ".json",
    ".css", ".js", ".webp", ".woff", ".woff2", ".eot", ".ttf", ".otf", ".mp4", ".txt"
]

def has_extension(url, extensions):
    parsed_url = urlparse(url)
    path = parsed_url.path
    extension = os.path.splitext(path)[1].lower()
    return extension in extensions

def clean_url(url):
    parsed_url = urlparse(url)
    if (parsed_url.port == 80 and parsed_url.scheme == "http") or (parsed_url.port == 443 and parsed_url.scheme == "https"):
        parsed_url = parsed_url._replace(netloc=parsed_url.netloc.rsplit(":", 1)[0])
    return parsed_url.geturl()

def clean_urls(urls, extensions, placeholder):
    cleaned_urls = set()
    for url in urls:
        cleaned_url = clean_url(url)
        if not has_extension(cleaned_url, extensions):
            parsed_url = urlparse(cleaned_url)
            query_params = parse_qs(parsed_url.query)
            cleaned_params = {key: placeholder for key in query_params}
            cleaned_query = urlencode(cleaned_params, doseq=True)
            cleaned_url = parsed_url._replace(query=cleaned_query).geturl()
            cleaned_urls.add(cleaned_url)
    return list(cleaned_urls)

def fetch_and_clean_urls(domain, extensions, stream_output, proxy, placeholder, output_file):
    logging.info(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Fetching URLs for {Fore.CYAN + domain + Style.RESET_ALL}")
    wayback_uri = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=txt&collapse=urlkey&fl=original&page=/"
    response = client.fetch_url_content(wayback_uri, proxy)
    urls = response.text.split()

    logging.info(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Found {Fore.GREEN + str(len(urls)) + Style.RESET_ALL} URLs for {Fore.CYAN + domain + Style.RESET_ALL}")

    cleaned_urls = clean_urls(urls, extensions, placeholder)
    logging.info(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Cleaning URLs for {Fore.CYAN + domain + Style.RESET_ALL}")
    logging.info(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Found {Fore.GREEN + str(len(cleaned_urls)) + Style.RESET_ALL} URLs after cleaning")

    with open(output_file, "a") as f:  # Append mode to write to the same file
        for url in cleaned_urls:
            if "?" in url:
                f.write(url + "\n")
                if stream_output:
                    print(url)

    logging.info(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Appended cleaned URLs to {Fore.CYAN + output_file + Style.RESET_ALL}")

def main():
    log_text = "Custom banner here"
    colored_log_text = f"{yellow_color_code}{log_text}{reset_color_code}"
    print(colored_log_text)
    parser = argparse.ArgumentParser(description="Mining URLs from dark corners of Web Archives")
    parser.add_argument("-d", "--domain", help="Domain name to fetch related URLs for.")
    parser.add_argument("-l", "--list", help="File containing a list of domain names.")
    parser.add_argument("-s", "--stream", action="store_true", help="Stream URLs on the terminal.")
    parser.add_argument("--proxy", help="Set the proxy address for web requests.", default=None)
    parser.add_argument("-p", "--placeholder", help="placeholder for parameter values", default="FUZZ")
    parser.add_argument("-o", "--output", required=True, help="Output file name to save all URLs.")
    args = parser.parse_args()

    if not args.domain and not args.list:
        parser.error("Please provide either the -d option or the -l option.")
    if args.domain and args.list:
        parser.error("Please provide either the -d option or the -l option, not both.")

    extensions = HARDCODED_EXTENSIONS
    output_file = args.output

    if args.domain:
        fetch_and_clean_urls(args.domain, extensions, args.stream, args.proxy, args.placeholder, output_file)
    elif args.list:
        with open(args.list, "r") as f:
            domains = [line.strip().lower().replace('https://', '').replace('http://', '') for line in f.readlines()]
            domains = [domain for domain in domains if domain]  # Remove empty lines
            domains = list(set(domains))  # Remove duplicates
            for domain in domains:
                fetch_and_clean_urls(domain, extensions, args.stream, args.proxy, args.placeholder, output_file)

if __name__ == "__main__":
    main()
