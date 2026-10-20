import { queryCollection } from "@nuxt/content/server";
import { contentNodes } from "~/utils/contentNodes";

export default defineEventHandler(async (event) => {
    const parameter = getRouterParam(event, "name");
    const name = parameter === undefined ? undefined : decodeURIComponent(parameter);

    if (name == "list" || name === undefined) {
        const contentQuery = await queryCollection(event, "content").all();
        return contentQuery.filter((page) => page.path?.startsWith("/sd-jwt-credentials/") && contentNodes(page.body).find((elem) => elem.tag === "pre" && elem.props?.language === "json") != undefined).map((elem) => elem.title);
    }

    const contentQuery = await queryCollection(event, "content").all();

    const matchedContent = contentQuery.find((content) => {
        return content.path?.startsWith("/sd-jwt-credentials/") && content.title === name;
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

    const code = contentNodes(matchedContent.body).find((elem) => {
        return elem.tag === "pre" && elem.props?.language === "json";
    })?.props?.code;

    return JSON.parse(String(code));
});
