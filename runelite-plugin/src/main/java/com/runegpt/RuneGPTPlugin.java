package com.runegpt;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import lombok.extern.slf4j.Slf4j;
import net.runelite.api.*;
import net.runelite.api.events.*;
import net.runelite.api.widgets.Widget;
import net.runelite.api.widgets.WidgetInfo;
import net.runelite.client.config.ConfigManager;
import net.runelite.client.eventbus.Subscribe;
import net.runelite.client.plugins.Plugin;
import net.runelite.client.plugins.PluginDescriptor;
import net.runelite.client.ui.overlay.OverlayManager;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import javax.inject.Inject;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@PluginDescriptor(
    name = "RuneGPT",
    description = "AI-powered game assistant",
    tags = {"ai", "assistant", "tutorial"},
    enabledByDefault = false
)
public class RuneGPTPlugin extends Plugin {
    private WebSocketClient webSocketClient;
    private final Gson gson = new Gson();
    private boolean isEnabled = false;

    @Inject
    private Client client;

    @Inject
    private ConfigManager configManager;

    @Inject
    private OverlayManager overlayManager;

    @Inject
    private RuneGPTConfig config;

    @Inject
    private RuneGPTOverlay overlay;

    @Override
    protected void startUp() {
        log.info("RuneGPT plugin started");
        overlayManager.add(overlay);
        if (config.enabled()) {
            connectWebSocket();
        }
    }

    @Override
    protected void shutDown() {
        log.info("RuneGPT plugin stopped");
        overlayManager.remove(overlay);
        if (webSocketClient != null) {
            webSocketClient.close();
        }
    }

    private void connectWebSocket() {
        try {
            webSocketClient = new WebSocketClient(new URI(config.websocketUrl())) {
                @Override
                public void onOpen(ServerHandshake handshakedata) {
                    log.info("WebSocket connection established");
                    isEnabled = true;
                }

                @Override
                public void onMessage(String message) {
                    log.debug("Received message: {}", message);
                    try {
                        JsonObject response = gson.fromJson(message, JsonObject.class);
                        if (response.has("suggestion")) {
                            overlay.setSuggestion(response.get("suggestion").getAsString());
                        }
                    } catch (Exception e) {
                        log.error("Failed to parse AI response: ", e);
                    }
                }

                @Override
                public void onClose(int code, String reason, boolean remote) {
                    log.info("WebSocket connection closed: {} - {}", code, reason);
                    isEnabled = false;
                    overlay.hide();
                }

                @Override
                public void onError(Exception ex) {
                    log.error("WebSocket error: ", ex);
                    isEnabled = false;
                    overlay.hide();
                }
            };
            webSocketClient.connect();
        } catch (Exception e) {
            log.error("Failed to connect to WebSocket server: ", e);
        }
    }

    private void sendGameState() {
        if (!isEnabled || webSocketClient == null || !webSocketClient.isOpen()) {
            return;
        }

        JsonObject gameState = new JsonObject();
        
        // Add chat messages if enabled
        if (config.collectChat()) {
            gameState.addProperty("latestChatMessage", getLatestChatMessage());
        }
        
        // Add tutorial widget text
        gameState.addProperty("tutorialText", getTutorialText());
        
        // Add inventory items if enabled
        if (config.collectInventory()) {
            gameState.add("inventory", gson.toJsonTree(getInventoryItems()));
        }
        
        // Add player location if enabled
        if (config.collectLocation()) {
            LocalPoint localPoint = client.getLocalPlayer().getLocalLocation();
            if (localPoint != null) {
                gameState.addProperty("playerX", localPoint.getX());
                gameState.addProperty("playerY", localPoint.getY());
            }
        }

        webSocketClient.send(gameState.toString());
    }

    private String getLatestChatMessage() {
        Widget chatBox = client.getWidget(WidgetInfo.CHATBOX_MESSAGE);
        return chatBox != null ? chatBox.getText() : "";
    }

    private String getTutorialText() {
        Widget tutorialWidget = client.getWidget(WidgetInfo.TUTORIAL_PROGRESS);
        return tutorialWidget != null ? tutorialWidget.getText() : "";
    }

    private List<String> getInventoryItems() {
        List<String> items = new ArrayList<>();
        ItemContainer inventory = client.getItemContainer(InventoryID.INVENTORY);
        if (inventory != null) {
            for (Item item : inventory.getItems()) {
                if (item.getId() != -1) {
                    String itemName = client.getItemDefinition(item.getId()).getName();
                    items.add(itemName);
                }
            }
        }
        return items;
    }

    @Subscribe
    public void onGameTick(GameTick event) {
        if (config.enabled()) {
            sendGameState();
        }
    }

    @Subscribe
    public void onChatMessage(ChatMessage event) {
        if (config.enabled() && config.collectChat()) {
            sendGameState();
        }
    }

    @Subscribe
    public void onMenuOptionClicked(MenuOptionClicked event) {
        if (config.enabled()) {
            sendGameState();
        }
    }

    @Subscribe
    public void onItemContainerChanged(ItemContainerChanged event) {
        if (config.enabled() && config.collectInventory() && 
            event.getContainerId() == InventoryID.INVENTORY.getId()) {
            sendGameState();
        }
    }
} 