
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

import org.littleshoot.proxy.HttpFilters;
import org.littleshoot.proxy.HttpFiltersAdapter;
import org.littleshoot.proxy.HttpFiltersSourceAdapter;
import org.littleshoot.proxy.HttpProxyServer;
import org.littleshoot.proxy.impl.DefaultHttpProxyServer;

import io.netty.channel.ChannelHandlerContext;
import io.netty.handler.codec.http.DefaultFullHttpResponse;
import io.netty.handler.codec.http.HttpContent;
import io.netty.handler.codec.http.HttpObject;
import io.netty.handler.codec.http.HttpRequest;
import io.netty.handler.codec.http.HttpResponse;
import io.netty.handler.codec.http.HttpResponseStatus;
import io.netty.handler.codec.http.LastHttpContent;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

// Helper class for sending alerts
class AlertNotifier {

    private static final OkHttpClient client = new OkHttpClient();
    private static final String ALERT_URL = "http://nginx/api/aemtd-alert";

    public void sendAlert(String reason) {
        String json = "{\"reason\": \"" + reason + "\"}";
        RequestBody body = RequestBody.create(json, MediaType.get("application/json; charset=utf-8"));
        Request request = new Request.Builder().url(ALERT_URL).post(body).build();
        try (Response response = client.newCall(request).execute()) {
            System.err.println("[ALERT] Sent notification to dashboard. Response: " + response.code());
        } catch (IOException e) {
            System.err.println("[ALERT] Failed to send notification to dashboard: " + e.getMessage());
        }

    }
}

public class AEMTDProxyServer {

    public static void main(String[] args) {
        final MicroserviceShuffler shuffler = new MicroserviceShuffler();
        final AlertNotifier notifier = new AlertNotifier();

        HttpProxyServer server = DefaultHttpProxyServer.bootstrap()
                .withPort(8080)
                .withFiltersSource(new HttpFiltersSourceAdapter() {
                    @Override
                    public HttpFilters filterRequest(HttpRequest originalRequest, ChannelHandlerContext ctx) {
                        return new HttpFiltersAdapter(originalRequest) {
                            private StringBuilder requestBody = new StringBuilder();

                            @Override
                            public InetSocketAddress proxyToServerResolutionStarted(String resolvingServerHostAndPort) {
                                return new InetSocketAddress("localhost", 80);
                            }

                            @Override
                            public HttpResponse clientToProxyRequest(HttpObject httpObject) {
                                if (httpObject instanceof HttpContent) {
                                    requestBody.append(((HttpContent) httpObject).content().toString(StandardCharsets.UTF_8));
                                }
                                if (httpObject instanceof LastHttpContent) {
                                    String attackReason = getAttackReason(requestBody.toString(), originalRequest);
                                    if (attackReason != null) {
                                        System.out.println("Threat Detected! Initiating Moving Target Defense...");

                                        // *** TRIGGER DEFENSE ACTIONS ***
                                        notifier.sendAlert(attackReason); // Send alert to dashboard!
                                        shuffler.containVictimService("frontend-app");
                                        shuffler.migrateService("payment-service");

                                        return new DefaultFullHttpResponse(originalRequest.getProtocolVersion(), HttpResponseStatus.FORBIDDEN);
                                    }
                                }
                                return null;
                            }

                            private String getAttackReason(String body, HttpRequest request) {
                                String userAgent = request.headers().get("User-Agent");
                                if (userAgent != null && userAgent.contains("MaliciousBot")) {
                                    return "Malicious User-Agent detected";
                                }
                                if (body != null && body.contains("lol lol lol")) {
                                    return "Malicious XML (Coercive Parsing) detected";
                                }
                                return null;
                            }
                        };
                    }

                    @Override
                    public int getMaximumRequestBufferSizeInBytes() {
                        return 2 * 1024 * 1024;
                    }
                })
                .start();
        System.out.println("AEMTD Proxy started on port 8080, forwarding to Nginx.");
    }
}
