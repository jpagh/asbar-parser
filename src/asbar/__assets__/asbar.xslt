<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<html>
<head>
<title>Messages</title>
<style>
    @font-face {
        font-family: 'Arial-Emoji';
        src: url('Arial-Emoji.ttf') format('truetype');
    }

    body {
        font-family: Arial-Emoji, Arial, Helvetica, sans-serif;
        font-size: small;
    }

    .messages {
        width: 800px;
        margin: auto;
    }

    .date {
        text-align: center;
        color: #b3b3b3;
    }

    .messages-cen {
        width: 50%;
        padding: 20px;
        display: block;
        background-color: #f2f2f2;
        border-radius: 20px 20px 20px 0px;
        margin-bottom: 25px;
        word-wrap: break-word
    }

    .messages-cen2 {
        width: 50%;
        padding: 20px;
        display: block;
        position: relative;
        left: 210px;
        background-color: #d2f6cb;
        border-radius: 20px 20px 0px 20px;
        margin-bottom: 25px;
        word-wrap: break-word
    }

    .messages-cen3 {
        color: #ffffff;
        width: 50%;
        padding: 20px;
        display: block;
        position: relative;
        left: 350px;
        background-color: #0078fe;
        border-radius: 20px 20px 0px 20px;
        margin-bottom: 25px;
        word-wrap: break-word
    }

    .del-messages-cen {
        width: 50%;
        padding: 20px;
        display: block;
        background-color: #f2f2f2;
        color: #ff0000;
        border-radius: 20px 20px 20px 0px;
        margin-bottom: 25px;
        word-wrap: break-word
    }

    .del-messages-cen2 {
        width: 50%;
        padding: 20px;
        display: block;
        position: relative;
        left: 210px;
        background-color: #d2f6cb;
        color: #ff0000;
        border-radius: 20px 20px 0px 20px;
        margin-bottom: 25px;
        word-wrap: break-word
    }

    .del-messages-cen3 {
        width: 50%;
        padding: 20px;
        display: block;
        position: relative;
        left: 210px;
        background-color: #0078fe;
        color: #ff0000;
        border-radius: 20px 20px 0px 20px;
        margin-bottom: 25px;
        word-wrap: break-word
    }
</style>
</head>

  <body>
    <p align="center" style="word-break:break-all;word-wrap:break-word"><font style="font-size:40px;font-family:Arial;color:#4D4D4D;">Messages</font></p>

    <div class="messages">

    <p>To: <xsl:value-of select="smses/sms/@contact_name"/> (<xsl:value-of select="smses/sms/@address"/>)</p>

      <xsl:for-each select="smses/*">
        <xsl:sort select="@contact_name"/>
        <xsl:sort select="@date"/>

        <p class="date"><xsl:value-of select="@readable_date"/></p>

        <xsl:if test="@type=1 or @type=2">
          <p>
            <xsl:attribute name="class">
              <xsl:if test="@type=1">messages-cen</xsl:if>
              <xsl:if test="@type=2">messages-cen3</xsl:if>
            </xsl:attribute>

            <xsl:value-of select="@body"/>
          </p>
        </xsl:if>

        <xsl:if test="@msg_box=1 or @msg_box=2">
          <p>
            <xsl:attribute name="class">
              <xsl:if test="@msg_box=1">messages-cen</xsl:if>
              <xsl:if test="@msg_box=2">messages-cen3</xsl:if>
            </xsl:attribute>

            <xsl:for-each select="parts/part">

              <xsl:if test="@seq=0 and @ct='image/jpeg'">
                <img width="400" align="middle">
                  <xsl:attribute name="src">
                    <xsl:value-of select="concat('data:',@ct,';base64,',@data)"/>
                  </xsl:attribute>
                </img>
              </xsl:if>

              <xsl:if test="@seq=0 and @ct='image/png'">
                <img width="400" align="middle">
                  <xsl:attribute name="src">
                    <xsl:value-of select="concat('data:',@ct,';base64,',@data)"/>
                  </xsl:attribute>
                </img>
              </xsl:if>

              <xsl:if test="@seq=0 and @ct='image/heic'">
                <img width="400" align="middle">
                  <xsl:attribute name="src">
                    <xsl:value-of select="concat(@cl,'.jpg')"/>
                  </xsl:attribute>
                </img>
              </xsl:if>

              <xsl:if test="@seq=0 and @ct='video/3gpp'">
                <a>
                  <xsl:attribute name="href">
                    <xsl:value-of select="concat(@cl,'.mp4')"/>
                  </xsl:attribute>
                  <img width="400" align="middle" type="image/jpg">
                    <xsl:attribute name="src">
                      <xsl:value-of select="concat(@cl,'.jpg')"/>
                    </xsl:attribute>
                  </img>
                </a>
              </xsl:if>

              <xsl:if test="@seq=0 and @ct='video/mp4'">
                <a>
                  <xsl:attribute name="href">
                    <xsl:value-of select="@cl"/>
                  </xsl:attribute>
                  <img width="400" align="middle" type="image/jpg">
                    <xsl:attribute name="src">
                      <xsl:value-of select="concat(@cl,'.jpg')"/>
                    </xsl:attribute>
                  </img>
                </a>
              </xsl:if>

              <xsl:if test="@seq=0 and @ct='audio/amr'">
                <audio width="400" align="middle" type="audio/mpeg">
                  <xsl:attribute name="src">
                    <xsl:value-of select="concat(@date,'-',@cl,'.mp3')"/>
                  </xsl:attribute>
                </audio>
              </xsl:if>

              <xsl:if test="@seq=0 and @ct='text/plain'">
                <xsl:value-of select="@text"/>
              </xsl:if>

            </xsl:for-each>

          </p>
        </xsl:if>
      </xsl:for-each>
    </div>
  </body>
</html>
</xsl:template>
</xsl:stylesheet>