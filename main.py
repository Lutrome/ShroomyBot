import argparse


def main():
    parser = argparse.ArgumentParser(description="Run a Discord bot")
    parser.add_argument("-t", "--test", help="set for bot to use local variables", action="store_true")
    args = parser.parse_args()
    if args.test:
        import beta
        beta.setup_env()
    from bot import shroomy_bot
    shroomy_bot.run()


if __name__ == '__main__':
    main()