import jinja2
import feedparser

def getBlogPosts():
    d = feedparser.parse('https://derekweitzel.com/feed.xml')
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(d)
    return d.entries[:5]

def main():
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "README.md.tmpl"
    template = templateEnv.get_template(TEMPLATE_FILE)

    posts = getBlogPosts()


    outputText = template.render(posts=posts)
    with open("README.md", 'w') as readme:
        readme.write(outputText)
    


if __name__ == "__main__":
    main()