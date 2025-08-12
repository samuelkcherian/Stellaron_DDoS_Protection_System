
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

public class AEMTDProxyServer {

    public static void main(String[] args) {
        final int localPort = 8080;
        final String targetServerHost = "localhost";
        final int targetServerPort = 80;

        System.out.println("Starting AEMTD Proxy on port: " + localPort);
        System.out.println("Forwarding traffic to NGINX at: " + targetServerHost + ":" + targetServerPort);

        HttpProxyServer server = DefaultHttpProxyServer.bootstrap()
                .withPort(localPort)
                .withFiltersSource(new HttpFiltersSourceAdapter() {
                    @Override
                    public HttpFilters filterRequest(HttpRequest originalRequest, ChannelHandlerContext ctx) {
                        return new HttpFiltersAdapter(originalRequest) {

                            private StringBuilder requestBody = new StringBuilder();

                            @Override
                            public InetSocketAddress proxyToServerResolutionStarted(String resolvingServerHostAndPort) {
                                return new InetSocketAddress(targetServerHost, targetServerPort);
                            }

                            // This method now has the correct return type logic
                            @Override
                            public HttpResponse clientToProxyRequest(HttpObject httpObject) {
                                if (httpObject instanceof HttpContent) {
                                    HttpContent content = (HttpContent) httpObject;
                                    requestBody.append(content.content().toString(StandardCharsets.UTF_8));
                                }
                                if (httpObject instanceof LastHttpContent) {
                                    if (isMaliciousXml(requestBody.toString())) {
                                        System.out.println("Threat Detected: Malicious XML content. Blocking request.");
                                        return new DefaultFullHttpResponse(
                                                originalRequest.getProtocolVersion(),
                                                HttpResponseStatus.FORBIDDEN
                                        );
                                    }
                                }
                                // THIS IS THE KEY CHANGE: Return null to allow the request to proceed.
                                return null;
                            }

                            private boolean isMaliciousXml(String body) {
                                if (body == null || body.isEmpty() || !body.trim().startsWith("<")) {
                                    return false; // Not XML or empty
                                }
                                if (body.contains("lol lol lol")) {
                                    return true; // Malicious pattern detected
                                }
                                return false;
                            }
                        };
                    }

                    @Override
                    public int getMaximumRequestBufferSizeInBytes() {
                        return 2 * 1024 * 1024; // 2MB buffer
                    }
                })
                .start();

        System.out.println("AEMTD Proxy with XML inspection started.");
    }
}
