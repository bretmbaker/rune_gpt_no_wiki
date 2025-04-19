package com.runegpt;

import lombok.extern.slf4j.Slf4j;
import net.runelite.client.ui.overlay.Overlay;
import net.runelite.client.ui.overlay.OverlayLayer;
import net.runelite.client.ui.overlay.OverlayPosition;
import net.runelite.client.ui.overlay.OverlayPriority;
import net.runelite.client.ui.overlay.components.PanelComponent;
import net.runelite.client.ui.overlay.components.TitleComponent;

import javax.inject.Inject;
import java.awt.*;

@Slf4j
public class RuneGPTOverlay extends Overlay {
    private final PanelComponent panelComponent = new PanelComponent();
    private String currentSuggestion = "";
    private boolean showOverlay = false;

    @Inject
    public RuneGPTOverlay() {
        setPosition(OverlayPosition.TOP_RIGHT);
        setLayer(OverlayLayer.ABOVE_WIDGETS);
        setPriority(OverlayPriority.HIGH);
    }

    @Override
    public Dimension render(Graphics2D graphics) {
        if (!showOverlay || currentSuggestion.isEmpty()) {
            return null;
        }

        panelComponent.getChildren().clear();

        // Add title
        panelComponent.getChildren().add(TitleComponent.builder()
            .text("RuneGPT Suggestion")
            .build());

        // Add suggestion text
        panelComponent.getChildren().add(() -> {
            graphics.setColor(Color.WHITE);
            graphics.drawString(currentSuggestion, 10, 20);
            return new Dimension(graphics.getFontMetrics().stringWidth(currentSuggestion) + 20, 30);
        });

        return panelComponent.render(graphics);
    }

    public void setSuggestion(String suggestion) {
        this.currentSuggestion = suggestion;
        this.showOverlay = !suggestion.isEmpty();
    }

    public void hide() {
        this.showOverlay = false;
    }
} 