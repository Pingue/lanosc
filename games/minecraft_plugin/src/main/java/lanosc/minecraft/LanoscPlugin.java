package lanosc.minecraft;

import com.google.gson.Gson;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerAdvancementDoneEvent;
import org.bukkit.event.player.PlayerDeathEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.plugin.java.JavaPlugin;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

public class LanoscPlugin extends JavaPlugin implements Listener {

    private String lanoscHost;
    private int lanoscPort;
    private final Gson gson = new Gson();

    @Override
    public void onEnable() {
        saveDefaultConfig();
        FileConfiguration cfg = getConfig();
        lanoscHost = cfg.getString("lanosc.host", "127.0.0.1");
        lanoscPort = cfg.getInt("lanosc.port", 10052);
        getServer().getPluginManager().registerEvents(this, this);
        getLogger().info("LANOSC bridge enabled -> udp://" + lanoscHost + ":" + lanoscPort);
    }

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        send("player_join", "player", event.getPlayer().getName());
    }

    @EventHandler
    public void onPlayerQuit(PlayerQuitEvent event) {
        send("player_leave", "player", event.getPlayer().getName());
    }

    @EventHandler
    public void onPlayerDeath(PlayerDeathEvent event) {
        send("player_death", "player", event.getEntity().getName());
    }

    @EventHandler
    public void onPlayerAdvancement(PlayerAdvancementDoneEvent event) {
        String ns = event.getAdvancement().getKey().getNamespace();
        if ("minecraft".equals(ns)) {
            send("advancement_unlock",
                    "player", event.getPlayer().getName(),
                    "advancement", event.getAdvancement().getKey().getKey());
        }
    }

    private void send(String eventName, String... kvPairs) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("event", eventName);
        payload.put("ts", System.currentTimeMillis() / 1000.0);
        for (int i = 0; i + 1 < kvPairs.length; i += 2) {
            payload.put(kvPairs[i], kvPairs[i + 1]);
        }
        byte[] data = gson.toJson(payload).getBytes(StandardCharsets.UTF_8);
        try (DatagramSocket socket = new DatagramSocket()) {
            InetAddress addr = InetAddress.getByName(lanoscHost);
            socket.send(new DatagramPacket(data, data.length, addr, lanoscPort));
        } catch (Exception e) {
            getLogger().warning("Failed to send LANOSC event '" + eventName + "': " + e.getMessage());
        }
    }
}
