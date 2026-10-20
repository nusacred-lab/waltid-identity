import { queryCollection } from "@nuxt/content/server";
import { contentNodes } from "~/utils/contentNodes";

export default defineEventHandler(async (event) => {
    const parameter = getRouterParam(event, "name");
    const name = parameter === undefined ? undefined : decodeURIComponent(parameter);
    if (name === undefined) {
        setResponseStatus(event, 400);
        return "error: No name set!";
    }

    const contentQuery = await queryCollection(event, "content").all();

    const matchedContent = contentQuery.find((content) => {
        return content.path?.startsWith("/w3c-credentials/") && content.title === name;
    });

    if (matchedContent === undefined) {
        const n = contentQuery
            .filter((content) => {
                return content.navigation === undefined;
            })
            .map((content) => {
                return content.title;
            });

        setResponseStatus(event, 400);
        return `error: No credential found named: \"${name}\". Available credentials: ${n.join(", ")}`;
    }



    const codeblocksAndTitles = contentNodes(matchedContent.body).filter((elem) => {
        return (elem.tag === "pre" && elem.props?.language === "json") || elem.tag === "h2";
    });

    if (!codeblocksAndTitles) {
        setResponseStatus(event, 400);
        return "error: no-credential";
    }

    let mappingInTitle = false;
    for (const codeblockOrTitle of codeblocksAndTitles) {


        if (
            codeblockOrTitle.tag === "h2" &&
            codeblockOrTitle?.children
                ?.find((c) => c.type === "text")
                ?.value?.toLowerCase()
                ?.includes("mapping") === true
        ) {
            mappingInTitle = true;
            continue;
        }

        if (mappingInTitle && codeblockOrTitle.tag === "pre" && codeblockOrTitle.props?.language === "json") {
            return JSON.parse(String(codeblockOrTitle.props.code));
        }
    }

    setResponseStatus(event, 400);
    return "error: no-mapping";
});
