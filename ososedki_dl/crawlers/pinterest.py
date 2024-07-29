import validators
import web_scrapper as web_scrapper

# TODO: Set data properly to allow call get(url, data=feed_data)


def get_user_input():
    try:
        pin = input("Enter a URL or a Pinterest pin or a pin ID: ")
        if pin.isdigit():
            pin_url = f"https://www.pinterest.com/pin/{pin}/"
        else:
            pin_url = pin

        if len(pin_url) == 0 or not validators.url(pin_url):
            print("Error, you must specify a valid url.")
            exit()

        max_depth = input(
            "How many related posts do you want to find? (from 0 to 2500): "
        )
        if not max_depth.isdigit():
            print("Error, you must specify a valid number.")
            exit()

        print("\n")

        return pin, pin_url, int(max_depth)
    except KeyboardInterrupt:
        return None, None, None


def pinterest_download(d, pin, pin_url, max_depth):
    if not all([pin, pin_url, max_depth]):
        return

    try:
        feed_url = f"https://www.pinterest.com/resource/RelatedPinFeedResource/get/?source_url={pin_url}"

        feed_payload = {
            "data": {
                "options": {
                    "field_set_key": "unauth_react",
                    "page_size": max_depth,
                    "pin": f"{pin}",
                    "prepend": False,
                    "add_vase": True,
                    "show_seo_canonical_pins": True,
                    "source": "unknown",
                    "top_level_source": "unknown",
                    "top_level_source_depth": 1,
                    "show_pdp": False,
                    "bookmarks": [
                        "Pz9DZ0FCQUFBQmhtbXN2QUVJQUFJQUFBQU1BZ0FFQUFnQUJnQUFBQUFBfGVkYzNlNzczNmFiMWQ0ZGViMjdjZDAzNTkxZGM4NWNjZGI2ZGEwZDZlN2JmNzNiYTIyYzUxNTM2ODZhMDVhYWJ8TkVXfA=="
                    ],
                },
            },
        }

        test = f"""https://www.pinterest.com/resource/RelatedPinFeedResource/get/?source_url={pin_url}&data={{"options":{{"field_set_key":"unauth_react","page_size":{max_depth},"pin":"{pin}","prepend":false,"add_vase":true,"show_seo_canonical_pins":true,"source":"unknown","top_level_source":"unknown","top_level_source_depth":1,"show_pdp":false,"bookmarks":["Pz9DZ0FCQUFBQmhtbXN2QUVJQUFJQUFBQU1BZ0FFQUFnQUJnQUFBQUFBfGVkYzNlNzczNmFiMWQ0ZGViMjdjZDAzNTkxZGM4NWNjZGI2ZGEwZDZlN2JmNzNiYTIyYzUxNTM2ODZhMDVhYWJ8TkVXfA=="]}}}}"""

        d.get_media(pin_url)
        response = d.get_media(test, data=feed_payload)

        download_list = d.get_related_posts(response)

        d.download_posts(download_list)

    except KeyboardInterrupt:
        return


def main():
    html_file = None
    download_path = "./media"

    d = web_scrapper.WebScrapper("Pinterest", download_path, html_file)

    # 600386194074397779
    pin, pin_url, max_depth = get_user_input()

    pinterest_download(d, pin, pin_url, max_depth)

    d.end_session()
