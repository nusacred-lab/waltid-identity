// Standalone verification of the vendored module, using the same catalog as the parent build.
dependencyResolutionManagement {
    repositories { mavenCentral() }
    versionCatalogs {
        create("identityLibs") { from(files("../../gradle/libs.versions.toml")) }
    }
}
rootProject.name = "nusacred-cose-java"
