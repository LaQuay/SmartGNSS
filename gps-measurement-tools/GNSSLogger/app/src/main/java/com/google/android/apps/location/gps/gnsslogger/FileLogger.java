/*
 * Copyright (C) 2017 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.google.android.apps.location.gps.gnsslogger;

import android.content.Context;
import android.content.Intent;
import android.location.GnssClock;
import android.location.GnssMeasurement;
import android.location.GnssMeasurementsEvent;
import android.location.GnssNavigationMessage;
import android.location.GnssStatus;
import android.location.Location;
import android.location.LocationManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.SystemClock;
import android.support.v4.BuildConfig;
import android.support.v4.content.FileProvider;
import android.util.Log;
import android.widget.Toast;
import com.google.android.apps.location.gps.gnsslogger.LoggerFragment.UIFragmentComponent;

//import org.apache.http.HttpResponse;
//import org.apache.http.client.HttpClient;
//import org.apache.http.client.methods.HttpPost;


import net.codejava.networking.MultipartUtility;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileFilter;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.Locale;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

/**
 * A GNSS logger to store information to a file.
 */
public class FileLogger implements GnssListener {

  private static final String TAG = "FileLogger";
  private static final String FILE_PREFIX = "gnss_log";
  private static final String ERROR_WRITING_FILE = "Problem writing to file.";
  private static final String COMMENT_START = "# ";
  private static final char RECORD_DELIMITER = ',';
  private static final String VERSION_TAG = "Version: ";

  private static final int MAX_FILES_STORED = 100;
  private static final int MINIMUM_USABLE_FILE_SIZE_BYTES = 1000;

  private final Context mContext;

  private final Object mFileLock = new Object();
  private BufferedWriter mFileWriter;
  private File mFile;

  private UIFragmentComponent mUiComponent;

  public synchronized UIFragmentComponent getUiComponent() {
    return mUiComponent;
  }

  public synchronized void setUiComponent(UIFragmentComponent value) {
    mUiComponent = value;
  }

  public FileLogger(Context context) {
    this.mContext = context;
  }

  /**
   * Start a new file logging process.
   */
  public void startNewLog() {
    synchronized (mFileLock) {
      File baseDirectory;
      String state = Environment.getExternalStorageState();
      if (Environment.MEDIA_MOUNTED.equals(state)) {
        baseDirectory = new File(Environment.getExternalStorageDirectory(), FILE_PREFIX);
        baseDirectory.mkdirs();
      } else if (Environment.MEDIA_MOUNTED_READ_ONLY.equals(state)) {
        logError("Cannot write to external storage.");
        return;
      } else {
        logError("Cannot read external storage.");
        return;
      }

      SimpleDateFormat formatter = new SimpleDateFormat("yyy_MM_dd_HH_mm_ss");
      Date now = new Date();
      String fileName = String.format("%s_%s.txt", FILE_PREFIX, formatter.format(now));
      File currentFile = new File(baseDirectory, fileName);
      String currentFilePath = currentFile.getAbsolutePath();
      BufferedWriter currentFileWriter;
      try {
        currentFileWriter = new BufferedWriter(new FileWriter(currentFile));
      } catch (IOException e) {
        logException("Could not open file: " + currentFilePath, e);
        return;
      }

      // initialize the contents of the file
      try {
        currentFileWriter.write(COMMENT_START);
        currentFileWriter.newLine();
        currentFileWriter.write(COMMENT_START);
        currentFileWriter.write("Header Description:");
        currentFileWriter.newLine();
        currentFileWriter.write(COMMENT_START);
        currentFileWriter.newLine();
        currentFileWriter.write(COMMENT_START);
        currentFileWriter.write(VERSION_TAG);
        String manufacturer = Build.MANUFACTURER;
        String model = Build.MODEL;
        String fileVersion =
            mContext.getString(R.string.app_version)
                + " Platform: "
                + Build.VERSION.RELEASE
                + " "
                + "Manufacturer: "
                + manufacturer
                + " "
                + "Model: "
                + model;
        currentFileWriter.write(fileVersion);
        currentFileWriter.newLine();
        currentFileWriter.write(COMMENT_START);
        currentFileWriter.newLine();
        currentFileWriter.write(COMMENT_START);
        currentFileWriter.write(
            "Raw,ElapsedRealtimeMillis,TimeNanos,LeapSecond,TimeUncertaintyNanos,FullBiasNanos,"
                + "BiasNanos,BiasUncertaintyNanos,DriftNanosPerSecond,DriftUncertaintyNanosPerSecond,"
                + "HardwareClockDiscontinuityCount,Svid,TimeOffsetNanos,State,ReceivedSvTimeNanos,"
                + "ReceivedSvTimeUncertaintyNanos,Cn0DbHz,PseudorangeRateMetersPerSecond,"
                + "PseudorangeRateUncertaintyMetersPerSecond,"
                + "AccumulatedDeltaRangeState,AccumulatedDeltaRangeMeters,"
                + "AccumulatedDeltaRangeUncertaintyMeters,CarrierFrequencyHz,CarrierCycles,"
                + "CarrierPhase,CarrierPhaseUncertainty,MultipathIndicator,SnrInDb,"
                + "ConstellationType,AgcDb,CarrierFrequencyHz");
        currentFileWriter.newLine();
        currentFileWriter.write(COMMENT_START);
        currentFileWriter.newLine();
        currentFileWriter.write(COMMENT_START);
        currentFileWriter.write(
            "Fix,Provider,Latitude,Longitude,Altitude,Speed,Accuracy,(UTC)TimeInMs");
        currentFileWriter.newLine();
        currentFileWriter.write(COMMENT_START);
        currentFileWriter.newLine();
        currentFileWriter.write(COMMENT_START);
        currentFileWriter.write("Nav,Svid,Type,Status,MessageId,Sub-messageId,Data(Bytes)");
        currentFileWriter.newLine();
        currentFileWriter.write(COMMENT_START);
        currentFileWriter.newLine();
      } catch (IOException e) {
        logException("Count not initialize file: " + currentFilePath, e);
        return;
      }

      if (mFileWriter != null) {
        try {
          mFileWriter.close();
        } catch (IOException e) {
          logException("Unable to close all file streams.", e);
          return;
        }
      }

      mFile = currentFile;
      mFileWriter = currentFileWriter;
      Toast.makeText(mContext, "File opened: " + currentFilePath, Toast.LENGTH_SHORT).show();

      // To make sure that files do not fill up the external storage:
      // - Remove all empty files
      FileFilter filter = new FileToDeleteFilter(mFile);
      for (File existingFile : baseDirectory.listFiles(filter)) {
        existingFile.delete();
      }
      // - Trim the number of files with data
      File[] existingFiles = baseDirectory.listFiles();
      int filesToDeleteCount = existingFiles.length - MAX_FILES_STORED;
      if (filesToDeleteCount > 0) {
        Arrays.sort(existingFiles);
        for (int i = 0; i < filesToDeleteCount; ++i) {
          existingFiles[i].delete();
        }
      }
    }
  }

  /**
   * Send the current log via email or other options selected from a pop menu shown to the user. A
   * new log is started when calling this function.
   */
  public void send() {
    if (mFile == null) {
      return;
    }

    Intent emailIntent = new Intent(Intent.ACTION_SEND);
    emailIntent.setType("*/*");
    emailIntent.putExtra(Intent.EXTRA_SUBJECT, "SensorLog");
    emailIntent.putExtra(Intent.EXTRA_TEXT, "");
    // attach the file
    Uri fileURI =
        FileProvider.getUriForFile(mContext, BuildConfig.APPLICATION_ID + ".provider", mFile);
    emailIntent.putExtra(Intent.EXTRA_STREAM, fileURI);
    //getUiComponent().startActivity(Intent.createChooser(emailIntent, "Send log.."));



/*

    String url = "http://localhost";
    //File file = new File(Environment.getExternalStorageDirectory().getAbsolutePath(),
    //        "yourfile");
    File file = new File(fileURI.getPath());
    try {
      HttpClient httpclient = new DefaultHttpClient();

      HttpPost httppost = new HttpPost(url);

      InputStreamEntity reqEntity = new InputStreamEntity(
              new FileInputStream(file), -1);
      reqEntity.setContentType("binary/octet-stream");
      reqEntity.setChunked(true); // Send in multiple parts if needed
      httppost.setEntity(reqEntity);
      HttpResponse response = httpclient.execute(httppost);
      //Do something with response...
      Toast.makeText(mContext, "HERE!!!", Toast.LENGTH_LONG).show();

    } catch (Exception e) {
      // show error
    }

*/
    try {
      //submitData(fileURI.getPath());
      submitData(mFile);
    } catch (Exception e){
      Log.e("MDP", "exception", e);
    }

    Toast.makeText(mContext, "Call API from here!!!"+fileURI.getPath()+"\n", Toast.LENGTH_LONG).show();

    if (mFileWriter != null) {
      try {
        mFileWriter.flush();
        mFileWriter.close();
        mFileWriter = null;
      } catch (IOException e) {
        logException("Unable to close all file streams.", e);
        return;
      }
    }
  }

  public boolean submitData2(String pathToFile) throws Exception{
    URL url = new URL("http://07a96f3e.ngrok.io");
    HttpURLConnection urlConnection = (HttpURLConnection) url.openConnection();
    try {
      InputStream in = new BufferedInputStream(urlConnection.getInputStream());
      //readStream(in);
    } finally {
      urlConnection.disconnect();
    }
    return true;
  }


//  public boolean submitData(String pathToFile) throws Exception{
  public boolean submitData(File mmfile) throws Exception{
    String charset = "UTF-8";
    File uploadFile1 = mmfile;
    //File uploadFile2 = new File("e:/Test/PIC2.JPG");
    String requestURL = "http://07a96f3e.ngrok.io/handle_form";


      MultipartUtility multipart = new MultipartUtility(requestURL, charset);

      multipart.addHeaderField("User-Agent", "CodeJava");
      multipart.addHeaderField("Test-Header", "Header-Value");

      multipart.addFormField("description", "Cool Pictures");
      multipart.addFormField("keywords", "Java,upload,Spring");

      multipart.addFilePart("fileUpload", uploadFile1);
      //multipart.addFilePart("fileUpload", uploadFile2);

      List<String> response = multipart.finish();

      System.out.println("SERVER REPLIED:");

      for (String line : response) {
        System.out.println(line);
      }

    return true;
  }


/*
  public boolean submitData(String pathToFile){
    String baseUrl = "http://localhost:8000";
    //Defining retrofit api service
    Retrofit retrofit = new Retrofit.Builder()
            .baseUrl(baseUrl)
            .addConverterFactory(GsonConverterFactory.create())
            .build();

    File file = new File(pathToFile);
    RequestBody requestBody = RequestBody.create(MediaType.parse("image/*"), file);
    MultipartBody.Part fileupload = MultipartBody.Part.createFormData("file", file.getName(), requestBody);
    RequestBody filename = RequestBody.create(MediaType.parse("text/plain"), file.getName());

    ApiService service = retrofit.create(ApiService.class);
    Call<PostResponse> call = service.postData(fileupload, filename);
    //calling the api
    call.enqueue(new Callback<PostResponse>() {
      @Override
      public void onResponse(Call<PostResponse> call, Response<PostResponse> response) {
        if(response.isSuccessful()){
          Toast.makeText(mContext, response.body().getSuccess(), Toast.LENGTH_LONG).show();
        }
      }

      @Override
      public void onFailure(Call<PostResponse> call, Throwable t) {
        Toast.makeText(mContext, t.getMessage(), Toast.LENGTH_LONG).show();
      }
    });
  }

  public static String convertStreamToString(InputStream is) throws Exception {
    BufferedReader reader = new BufferedReader(new InputStreamReader(is));
    StringBuilder sb = new StringBuilder();
    String line = null;
    while ((line = reader.readLine()) != null) {
      sb.append(line).append("\n");
    }
    reader.close();
    return sb.toString();
  }

  public static String getStringFromFile (String filePath) throws Exception {
    File fl = new File(filePath);
    FileInputStream fin = new FileInputStream(fl);
    String ret = convertStreamToString(fin);
    //Make sure you close all streams.
    fin.close();
    return ret;
  }
*/

  @Override
  public void onProviderEnabled(String provider) {}

  @Override
  public void onProviderDisabled(String provider) {}

  @Override
  public void onLocationChanged(Location location) {
    if (location.getProvider().equals(LocationManager.GPS_PROVIDER)) {
      synchronized (mFileLock) {
        if (mFileWriter == null) {
          return;
        }
        String locationStream =
            String.format(
                Locale.US,
                "Fix,%s,%f,%f,%f,%f,%f,%d",
                location.getProvider(),
                location.getLatitude(),
                location.getLongitude(),
                location.getAltitude(),
                location.getSpeed(),
                location.getAccuracy(),
                location.getTime());
        try {
          mFileWriter.write(locationStream);
          mFileWriter.newLine();
        } catch (IOException e) {
          logException(ERROR_WRITING_FILE, e);
        }
      }
    }
  }

  @Override
  public void onLocationStatusChanged(String provider, int status, Bundle extras) {}

  @Override
  public void onGnssMeasurementsReceived(GnssMeasurementsEvent event) {
    synchronized (mFileLock) {
      if (mFileWriter == null) {
        return;
      }
      GnssClock gnssClock = event.getClock();
      for (GnssMeasurement measurement : event.getMeasurements()) {
        try {
          writeGnssMeasurementToFile(gnssClock, measurement);
        } catch (IOException e) {
          logException(ERROR_WRITING_FILE, e);
        }
      }
    }
  }

  @Override
  public void onGnssMeasurementsStatusChanged(int status) {}

  @Override
  public void onGnssNavigationMessageReceived(GnssNavigationMessage navigationMessage) {
    synchronized (mFileLock) {
      if (mFileWriter == null) {
        return;
      }
      StringBuilder builder = new StringBuilder("Nav");
      builder.append(RECORD_DELIMITER);
      builder.append(navigationMessage.getSvid());
      builder.append(RECORD_DELIMITER);
      builder.append(navigationMessage.getType());
      builder.append(RECORD_DELIMITER);

      int status = navigationMessage.getStatus();
      builder.append(status);
      builder.append(RECORD_DELIMITER);
      builder.append(navigationMessage.getMessageId());
      builder.append(RECORD_DELIMITER);
      builder.append(navigationMessage.getSubmessageId());
      byte[] data = navigationMessage.getData();
      for (byte word : data) {
        builder.append(RECORD_DELIMITER);
        builder.append(word);
      }
      try {
        mFileWriter.write(builder.toString());
        mFileWriter.newLine();
      } catch (IOException e) {
        logException(ERROR_WRITING_FILE, e);
      }
    }
  }

  @Override
  public void onGnssNavigationMessageStatusChanged(int status) {}

  @Override
  public void onGnssStatusChanged(GnssStatus gnssStatus) {}

  @Override
  public void onNmeaReceived(long timestamp, String s) {
    synchronized (mFileLock) {
      if (mFileWriter == null) {
        return;
      }
      String nmeaStream = String.format(Locale.US, "NMEA,%s,%d", s.trim(), timestamp);
      try {
        mFileWriter.write(nmeaStream);
        mFileWriter.newLine();
      } catch (IOException e) {
        logException(ERROR_WRITING_FILE, e);
      }
    }
  }

  @Override
  public void onListenerRegistration(String listener, boolean result) {}

  @Override
  public void onTTFFReceived(long l) {}

  private void writeGnssMeasurementToFile(GnssClock clock, GnssMeasurement measurement)
      throws IOException {
    String clockStream =
        String.format(
            "Raw,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s",
            SystemClock.elapsedRealtime(),
            clock.getTimeNanos(),
            clock.hasLeapSecond() ? clock.getLeapSecond() : "",
            clock.hasTimeUncertaintyNanos() ? clock.getTimeUncertaintyNanos() : "",
            clock.getFullBiasNanos(),
            clock.hasBiasNanos() ? clock.getBiasNanos() : "",
            clock.hasBiasUncertaintyNanos() ? clock.getBiasUncertaintyNanos() : "",
            clock.hasDriftNanosPerSecond() ? clock.getDriftNanosPerSecond() : "",
            clock.hasDriftUncertaintyNanosPerSecond()
                ? clock.getDriftUncertaintyNanosPerSecond()
                : "",
            clock.getHardwareClockDiscontinuityCount() + ",");
    mFileWriter.write(clockStream);

    String measurementStream =
        String.format(
            "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s",
            measurement.getSvid(),
            measurement.getTimeOffsetNanos(),
            measurement.getState(),
            measurement.getReceivedSvTimeNanos(),
            measurement.getReceivedSvTimeUncertaintyNanos(),
            measurement.getCn0DbHz(),
            measurement.getPseudorangeRateMetersPerSecond(),
            measurement.getPseudorangeRateUncertaintyMetersPerSecond(),
            measurement.getAccumulatedDeltaRangeState(),
            measurement.getAccumulatedDeltaRangeMeters(),
            measurement.getAccumulatedDeltaRangeUncertaintyMeters(),
            measurement.hasCarrierFrequencyHz() ? measurement.getCarrierFrequencyHz() : "",
            measurement.hasCarrierCycles() ? measurement.getCarrierCycles() : "",
            measurement.hasCarrierPhase() ? measurement.getCarrierPhase() : "",
            measurement.hasCarrierPhaseUncertainty()
                ? measurement.getCarrierPhaseUncertainty()
                : "",
            measurement.getMultipathIndicator(),
            measurement.hasSnrInDb() ? measurement.getSnrInDb() : "",
            measurement.getConstellationType(),
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
            && measurement.hasAutomaticGainControlLevelDb()
                ? measurement.getAutomaticGainControlLevelDb()
                : "",
            measurement.hasCarrierFrequencyHz() ? measurement.getCarrierFrequencyHz() : "");
    mFileWriter.write(measurementStream);
    mFileWriter.newLine();
  }

  private void logException(String errorMessage, Exception e) {
    Log.e(GnssContainer.TAG + TAG, errorMessage, e);
    Toast.makeText(mContext, errorMessage, Toast.LENGTH_LONG).show();
  }

  private void logError(String errorMessage) {
    Log.e(GnssContainer.TAG + TAG, errorMessage);
    Toast.makeText(mContext, errorMessage, Toast.LENGTH_LONG).show();
  }

  /**
   * Implements a {@link FileFilter} to delete files that are not in the
   * {@link FileToDeleteFilter#mRetainedFiles}.
   */
  private static class FileToDeleteFilter implements FileFilter {
    private final List<File> mRetainedFiles;

    public FileToDeleteFilter(File... retainedFiles) {
      this.mRetainedFiles = Arrays.asList(retainedFiles);
    }

    /**
     * Returns {@code true} to delete the file, and {@code false} to keep the file.
     *
     * <p>Files are deleted if they are not in the {@link FileToDeleteFilter#mRetainedFiles} list.
     */
    @Override
    public boolean accept(File pathname) {
      if (pathname == null || !pathname.exists()) {
        return false;
      }
      if (mRetainedFiles.contains(pathname)) {
        return false;
      }
      return pathname.length() < MINIMUM_USABLE_FILE_SIZE_BYTES;
    }
  }
}
