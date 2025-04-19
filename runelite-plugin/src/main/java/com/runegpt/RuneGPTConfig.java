package com.runegpt;

import net.runelite.client.config.Config;
import net.runelite.client.config.ConfigGroup;
import net.runelite.client.config.ConfigItem;
import net.runelite.client.config.ConfigSection;

@ConfigGroup("runegpt")
public interface RuneGPTConfig extends Config {
    @ConfigSection(
        name = "General Settings",
        description = "General plugin settings",
        position = 0
    )
    String generalSection = "general";

    @ConfigItem(
        keyName = "enabled",
        name = "Enable RuneGPT",
        description = "Enable or disable the RuneGPT plugin",
        section = generalSection,
        position = 0
    )
    default boolean enabled() {
        return false;
    }

    @ConfigItem(
        keyName = "websocketUrl",
        name = "WebSocket URL",
        description = "The WebSocket URL to connect to the RuneGPT backend",
        section = generalSection,
        position = 1
    )
    default String websocketUrl() {
        return "ws://localhost:8765";
    }

    @ConfigSection(
        name = "Data Collection",
        description = "Settings for what game data to collect",
        position = 1
    )
    String dataSection = "data";

    @ConfigItem(
        keyName = "collectChat",
        name = "Collect Chat Messages",
        description = "Collect and send chat messages to RuneGPT",
        section = dataSection,
        position = 0
    )
    default boolean collectChat() {
        return true;
    }

    @ConfigItem(
        keyName = "collectInventory",
        name = "Collect Inventory",
        description = "Collect and send inventory items to RuneGPT",
        section = dataSection,
        position = 1
    )
    default boolean collectInventory() {
        return true;
    }

    @ConfigItem(
        keyName = "collectLocation",
        name = "Collect Location",
        description = "Collect and send player location to RuneGPT",
        section = dataSection,
        position = 2
    )
    default boolean collectLocation() {
        return true;
    }
} 